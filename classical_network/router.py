from typing import Tuple
from classical_network.connection import ClassicConnection
from classical_network.enum import PacketType
from classical_network.node import ClassicalNode
from classical_network.packet import ClassicDataPacket
from classical_network.presets.connection_presets import DEFAULT_PRESET
from core.base_classes import World, Zone
from core.enums import InfoEventType, NodeType, SimulationEventType
from core.exceptions import NotConnectedError
from core.network import Network
from classical_network.routing import InternetExchange, RouteTable
from utils.mtu_fragmentation import fragment_packet, reassemble_fragments


class ClassicalRouter(ClassicalNode):
    def __init__(
        self,
        address: str,
        location: Tuple[int, int],
        network: Network,
        zone: Zone | World = None,
        name="",
        description="",
    ):
        super().__init__(
            NodeType.CLASSICAL_ROUTER,
            location,
            address,
            network,
            zone,
            name,
            description,
        )
        self.routing_table = RouteTable()
        self.default_gateway = InternetExchange.get_instance()
        isp_connection = ClassicConnection(self, self.default_gateway, DEFAULT_PRESET)
        self.add_connection(isp_connection)

    def update_local_routing_table(self, node_1, node_2):
        self.routing_table.add_edge(node_1, node_2)

    def add_connection(self, connection: ClassicConnection):
        super().add_connection(connection)

        self.update_local_routing_table(connection.node_1, connection.node_2)
        self.default_gateway.add_connection(connection)

    def forward(self):
        for node_2, buffer in self.buffers.items():
            while not buffer.empty():
                packet = buffer.get()

                if packet.next_hop == self:
                    self.receive_packet(packet)
                else:
                    print(f"Unexpected packet '{packet}' received from {node_2}")

    def receive_packet(self, packet: ClassicDataPacket):
        packet.append_hop(self)
        if packet.type == PacketType.DATA:
            self._send_update(SimulationEventType.PACKET_RECEIVED, packet=packet)
            if packet.get_header('fragment_id'):
                self._handle_fragment(packet)
            else:
                self.route_packet(packet)
    
    def _handle_fragment(self, packet: ClassicDataPacket):
        if not hasattr(self, 'fragment_buffer'):
            self.fragment_buffer = {}
        
        frag_id = packet.get_header('fragment_id')
        if frag_id not in self.fragment_buffer:
            self.fragment_buffer[frag_id] = []
        
        self.fragment_buffer[frag_id].append(packet)
        
        fragments = self.fragment_buffer[frag_id]
        self._send_update(SimulationEventType.INFO, data=dict(type=InfoEventType.FRAGMENT_RECEIVED, fragment_id=frag_id, message=f"Fragment {frag_id}/{len(fragments)} fragments received."))
        if any(not frag.get_header('more_fragments') for frag in fragments):
            reassembled = reassemble_fragments(fragments)
            if reassembled:
                self._send_update(SimulationEventType.INFO, data=dict(type=InfoEventType.FRAGMENT_REASSEMBLED, fragment_id=frag_id, message=f"Fragment {frag_id}/{len(fragments)} fragments reassembled."))
                del self.fragment_buffer[frag_id]
                self.receive_packet(reassembled.data)

    def route_packet(self, packet: ClassicDataPacket):
        direct_connection = self.get_connection(self, packet.to_address)

        if direct_connection:
            packet.next_hop = packet.to_address
            direct_connection.transmit_packet(packet)
            return

        shortest_path = self.default_gateway.get_path(self, packet.to_address)

        if len(shortest_path) <= 1:
            raise NotConnectedError(self, packet.to_address)

        next_hop = shortest_path[1]

        packet.next_hop = next_hop
        next_connection = self.get_connection(self, next_hop)

        if not next_connection:
            raise NotConnectedError(self, next_hop)

        
        if next_connection.mtu != -1 and packet.size_bytes > next_connection.mtu:
            fragments = fragment_packet(packet, next_connection.mtu)
            self._send_update(SimulationEventType.INFO, data=dict(type=InfoEventType.PACKET_FRAGMENTED, message=f"Packet fragmented into {len(fragments)} fragments because MTU is {next_connection.mtu} bytes."))
            for fragment in fragments:
                next_connection.transmit_packet(fragment)
        else:
            next_connection.transmit_packet(packet)

        self._send_update(SimulationEventType.PACKET_ROUTED, packet=packet)

    def __name__(self):
        return f"Router - '{self.name}'"

    def __repr__(self):
        return self.__name__()
