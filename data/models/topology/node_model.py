from typing import List, Optional, Tuple, Literal
from pydantic import BaseModel, Field


class ConnectionModal(BaseModel):
    """Network connection between hosts"""

    from_node: str = Field(
        description="Name of the host from which the connection originates"
    )
    to_node: str = Field(description="Name of the host to which the connection ends")
    length: float = Field(description="Length of the connection in kilometers")
    loss_per_km: float = Field(description="Loss per kilometer of the connection")
    name: str = Field(description="Name of the connection")

    # Quantum Connection specific fields
    noise_model: Optional[Literal['none', 'transmutation', 'depolarizing', 'amplitude_damping', 'phase_damping', 'default']] = Field(
        description="Noise model for the connection",
        default='none',
    )

    noise_strength: Optional[float] = Field(
        default=0.01,
        description="Strength of the noise applied to the connection (If applicable)",
        ge=0.0,
        le=1.0,
    )

    # Quantum Host specific fields
    error_rate_threshold: Optional[float] = Field(
        default=10,
        description="Error rate threshold for quantum hosts",
        ge=1,
        le=100,
    )
    qbits: Optional[int] = Field(
        default=128,
        description="Number number of qbits the host will generate",
        ge=16,
        multiple_of=8,
        le=1024,
    )

    # Classical Connection specific fields
    bandwidth: int = Field(description="Bandwidth of the connection in Mbps")
    latency: float = Field(description="Latency of the connection in milliseconds")
    packet_loss_rate: Optional[float] = Field(
        default=0.1,
        description="Packet loss rate for classical connections",
        ge=0,
        le=1,
    )
    packet_error_rate: Optional[float] = Field(
        default=0.1,
        description="Packet error rate for classical connections",
        ge=0,
        le=1,
    )
    mtu: int = Field(description="Maximum Transmission Unit for classical connections", default=1500)
    connection_config_preset: Optional[str] = Field(
        default=None,
        description="Connection configuration preset for quantum hosts",
        max_length=255,
    )


HOST_TYPES = Literal[
    "ClassicalHost",
    "ClassicalRouter",
    "QuantumHost",
    "QuantumRepeater",
    "QuantumAdapter",
    "ClassicToQuantumConverter",
    "QuantumToClassicConverter",
    "InternetExchange",
    "ClassicalNetwork",
    "Zone",
]


class HostModal(BaseModel):
    """Base class for network hosts"""

    name: str = Field(description="Name of the host")
    type: HOST_TYPES = Field(description="Type of the host")
    address: Optional[str] = Field(
        description="Address of the host. This can be IP/Hostname"
    )
    location: Tuple[float, float] = Field(
        description="Location of the host in (x, y) coordinates"
    )


class NetworkModal(BaseModel):
    """Network containing hosts and connections"""
    name: str = Field(description="Name of the network")
    address: Optional[str] = Field(description="Address of the network. This can be IP/Hostname")
    type: Literal["CLASSICAL_NETWORK", "QUANTUM_NETWORK"]
    location: Tuple[float, float] = Field(
        description="Location of the network in (x, y) coordinates"
    )
    hosts: List[HostModal] = Field(description="List of hosts within the network")
    connections: List[ConnectionModal] = Field(
        description="List of connections within the network"
    )


class AdapterModal(BaseModel):
    """Quantum adapter connecting classical and quantum networks"""

    name: str = Field(description="Name of the adapter")
    type: str = Field(description="Type of the adapter (e.g., QUMO, CNOT)")
    # size: Optional[Tuple[float, float]] = Field(description="Size of the adapter in (x, y) coordinates")
    address: str = Field(description="Address of the host. This can be IP/Hostname")
    location: Tuple[float, float] = Field(
        description="Location of the adapter in (x, y) coordinates"
    )
    quantumHost: str = Field(
        description="Address of the host where the quantum network is connected"
    )
    classicalHost: str = Field(
        description="Address of the host where the classical network is connected"
    )
    classicalNetwork: str = Field(description="Name of the classical network")
    quantumNetwork: str = Field(description="Name of the quantum network")
