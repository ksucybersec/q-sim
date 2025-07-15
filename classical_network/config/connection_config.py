from dataclasses import dataclass

@dataclass(frozen=True)
class ConnectionConfig:
    """
    Configuration parameters for a classical network connection.
    These values are typically used to instantiate a ClassicConnection object.
    """
    bandwidth: float  # Bits per second (bps)
    latency: float    # Seconds
    packet_loss_rate: float = 0.0  # Probability (0.0 to 1.0)
    packet_error_rate: float = 0.0 # Probability (0.0 to 1.0)
    mtu: int = 1500   # Bytes
    name_prefix: str = "conn" # Prefix for automatically generated connection names
    description: str = "" # Default description for connections using this config

    # def __post_init__(self):
    #     # Basic validation
    #     if self.bandwidth <= 0:
    #         raise ValueError("Bandwidth must be positive.")
    #     if self.latency < 0:
    #         raise ValueError("Latency cannot be negative.")
    #     if not (0.0 <= self.packet_loss_rate <= 1.0):
    #         raise ValueError("Packet loss rate must be between 0.0 and 1.0.")
    #     if not (0.0 <= self.packet_error_rate <= 1.0):
    #         raise ValueError("Packet error rate must be between 0.0 and 1.0.")
    #     if self.mtu <= 0:
    #         raise ValueError("MTU must be positive.")
        
    def to_dict(self) -> dict:
        return {
            "bandwidth": self.bandwidth if self.bandwidth != float('inf') else -1,
            "latency": self.latency,
            "packet_loss_rate": self.packet_loss_rate,
            "packet_error_rate": self.packet_error_rate,
            "mtu": self.mtu,
            "name_prefix": self.name_prefix,
            "description": self.description
        }

# --- Helper function to create descriptions ---
def _generate_description(medium_type: str, bw_mbps: float, lat_ms: float, loss: float, error: float, mtu: int) -> str:
    return (f"{medium_type} Link: {bw_mbps:.1f} Mbps, {lat_ms:.2f} ms latency, "
            f"{loss*100:.2f}% loss, {error*100:.2f}% error, MTU {mtu}B")