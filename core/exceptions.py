from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.base_classes import Node
    from core.network import Network


class QueSimException(Exception):
    pass


class UnSupportedNetworkError(QueSimException):

    def __init__(self, network: Network, node: Node):
        self.message = f"Unsupported network type. Network {network.name} is of type {network.network_type}. Node {node.name} excepticts otherwise."
        super().__init__(self.message)


class NotConnectedError(QueSimException):

    def __init__(self, node_1: Node, node_2: Node):
        self.message = f"Connection not found between {node_1.name} and {node_2.name}"
        super().__init__(self.message)


class DefaultGatewayNotFound(QueSimException):

    def __init__(self, node: Node):
        self.message = f"Default gateway not found for node {node.name}"
        super().__init__(self.message)


class BufferNotAssigned(QueSimException):

    def __init__(self, from_node: Node, to_node: Node):
        self.message = f"Buffer not assigned for {from_node.name} in {to_node.name}"
        super().__init__(self.message)


class QuantumChannelDoesNotExists(QueSimException):

    def __init__(self, q_host):
        self.message = f"Quantum Channel does not exists on Qhost {q_host}"
        super().__init__(self.message)


class QubitLossError(QueSimException):

    def __init__(self, channel, qbit):
        self.message = (
            f"Qbit Lost due to accumilated loss. Channel {channel}. Qbit: {qbit}"
        )
        super().__init__(self.message)


class PairAdapterAlreadyExists(QueSimException):

    def __init__(self, q_adapter, pair):
        self.message = f"Pair adapter ({pair}) already exists for adapter {q_adapter}."
        super().__init__(self.message)


class PairAdapterDoesNotExists(QueSimException):

    def __init__(self, q_adapter):
        self.message = f"Pair adapter does not exists exists for adapter {q_adapter}."
        super().__init__(self.message)


class NodesNotFound(QueSimException):

    def __init__(self, *args):
        self.message = f"Node not found."
        super().__init__(*args)


class ConnectionDownError(Exception):
    """Raised when attempting to transmit over a link that is down."""

    pass


class MtuExceededError(Exception):
    """Raised when a packet's size exceeds the connection's MTU."""

    def __init__(self, packet_id, packet_size, mtu, connection_name):
        self.packet_id = packet_id
        self.packet_size = packet_size
        self.mtu = mtu
        self.connection_name = connection_name
        super().__init__(
            f"Packet id {packet_id} (size {packet_size}B) on connection '{connection_name}' exceeds MTU ({self.mtu}B)."
        )


class RoutingError(Exception):
    """Raised for issues determining packet destination on the link."""

    pass
