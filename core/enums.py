import enum


class ZoneType(enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    SECURE = "secure"
    # Add more types as needed

class NodeType(enum.Enum):
    INTERNET_EXCHANGE = "internet_exchange"
    CLASSICAL_HOST = "classical_host"
    CLASSICAL_ROUTER = "classical_router"
    C2Q_CONVERTER = "c2q_converter"
    Q2C_CONVERTER = "q2c_converter"
    QUANTUM_HOST = "quantum_host"
    QUANTUM_REPEATER = "quantum_repeater"
    NETWORK = "network"
    QUANTUM_ADAPTER = "quantum_adapter"

class NetworkType(enum.Enum):
    QUANTUM_NETWORK = "quantum_network"
    CLASSICAL_NETWORK = "classical_network"

class SimulationEventType(enum.Enum):
    TRANSMISSION_STARTED = "transmission_started"
    PACKET_TRANSMITTED = "packet_transmitted"
    PACKET_RECEIVED = "packet_received"
    PACKET_LOTS = "packet_lost"
    PACKET_CORRUPTED = "packet_corrupted"
    PACKET_DROPPED = "packet_dropped"
    DATA_SENT = "data_sent"
    INFO = "info"
    DATA_RECEIVED = "data_received"
    PACKET_ROUTED = "packet_routed"
    ROUTING_ERROR = "routing_error"
    PACKET_DELIVERED = "packet_delivered"
    TRANSMISSION_FAILED = "transmission_failed"
    QKD_INITIALIZED = "qkd_initiated"
    CLASSICAL_DATA_RECEIVED = "classical_data_received"

class InfoEventType(enum.Enum):
    PACKET_FRAGMENTED = "packet_fragmented"
    FRAGMENT_RECEIVED = "fragment_received"
    FRAGMENT_REASSEMBLED = "fragment_reassembled"