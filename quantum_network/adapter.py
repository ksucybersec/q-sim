from queue import Queue
import time
from typing import List, Tuple
import qutip as qt
from classical_network.connection import ClassicConnection
from classical_network.enum import PacketType
from classical_network.packet import ClassicDataPacket
from classical_network.presets.connection_presets import DEFAULT_PRESET, GIGABIT_ETHERNET
from classical_network.router import ClassicalRouter
from core.base_classes import Node, World, Zone
from core.enums import InfoEventType, NodeType, NetworkType, SimulationEventType
from core.exceptions import (
    DefaultGatewayNotFound,
    NotConnectedError,
    PairAdapterAlreadyExists,
    PairAdapterDoesNotExists,
    QuantumChannelDoesNotExists,
    UnSupportedNetworkError,
)
from core.network import Network

# from quantum_network.channel import QuantumChannel
from quantum_network.host import QuantumHost
from quantum_network.packet import QKDTransmissionPacket
from utils.mtu_fragmentation import fragment_packet
from utils.simple_encryption import simple_xor_decrypt, simple_xor_encrypt

# from quantum_network.node import QuantumNode
# from quantum_network.repeater import QuantumRepeater
# from classical_network.router import ClassicalRouter


class QuantumAdapter(Node):
    def __init__(
        self,
        address: str,
        classical_network: Network,
        quantum_network: Network,
        location: Tuple,
        paired_adapter: "QuantumAdapter",
        quantum_host: QuantumHost,
        zone=None,
        name="",
        description="",
    ):
        super().__init__(address, location, classical_network, zone, name, description)
        self.type = NodeType.QUANTUM_ADAPTER
        self.classical_network = classical_network
        self.quantum_network = quantum_network
        self.input_data_buffer = Queue()

        self.shared_key = None  # Store the shared secret key here

        self.local_quantum_host = quantum_host
        self.local_quantum_host.send_classical_data = self.send_classical_data
        self.local_quantum_host.qkd_completed_fn = self.on_qkd_established
        self.local_classical_router = ClassicalRouter(
            f"InternalQCRouter{self.name}",
            self.location,
            self.classical_network,
            self.zone,
            f"QC_Router_{self.name}",
        )
        self.local_classical_router.route_packet = self.intercept_route_packet

        self.paired_adapter = paired_adapter  # Reference to the paired adapter
        if paired_adapter:
            # TODO: Add connection config
            connection = ClassicConnection(
                self.local_classical_router,
                self.paired_adapter.local_classical_router,
                DEFAULT_PRESET,
                name="QC_Router_Connection",
            )
            self.local_classical_router.add_connection(connection)
            self.paired_adapter.local_classical_router.add_connection(connection)

        if paired_adapter and (
            not self.local_quantum_host.channel_exists(
                paired_adapter.local_quantum_host
            )
        ):
            raise QuantumChannelDoesNotExists(self)

    def add_paired_adapter(self, adapter: "QuantumAdapter"):
        if self.paired_adapter:
            raise PairAdapterAlreadyExists(self, self.paired_adapter)

        self.paired_adapter = adapter

    def on_qkd_established(self, key: List[int]):
        self.shared_key = key
        self.logger.debug(f"QKD Established {key}")

        while not self.input_data_buffer.empty():
            packet = self.input_data_buffer.get()
            self.receive_packet(packet)

    def calculate_distance(self, node1, node2):
        # Simple Euclidean distance calculation, adjust as needed for your network topology
        x1, y1 = node1.location
        x2, y2 = node2.location
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def initiate_qkd(self):
        # Initiate QKD with the paired adapter
        if self.paired_adapter:
            self.local_quantum_host.perform_qkd()
            self._send_update(SimulationEventType.QKD_INITIALIZED, with_adapter=self.paired_adapter)
        else:
            self.logger.debug(f"{self.name} has no paired adapter to perform QKD.")
            raise PairAdapterDoesNotExists(self)

    def receive_packet(self, packet: ClassicDataPacket | QKDTransmissionPacket):
        # If the packet was last sent by pair adapter and  is type of classical packet, that packet was result of QKD encryption
        if (
            packet.hops[-2] == self.paired_adapter.local_classical_router
            and type(packet) == ClassicDataPacket
        ):
            self.process_packet(packet)
        elif type(packet) == QKDTransmissionPacket:
            self.local_quantum_host.receive_classical_data(packet.data)
        else:
            # Check if a QKD process needs to be initiated or if a key exists
            if self.shared_key is None and self.paired_adapter is not None:

                self.initiate_qkd()
                self.input_data_buffer.put(packet)
                return

            # If the packet is for the paired adapter, check if a key exists and then encrypt and forward
            if self.paired_adapter and packet.to_address == self.local_classical_router:
                if self.shared_key:
                    packet = self.encrypt_packet(packet)
                    self.forward_packet(packet, self.paired_adapter.local_classical_router)
                else:
                    print(
                        f"Time: {self.network.world.time:.2f}, {self.name} cannot forward packet, no shared key with {self.paired_adapter.name}"
                    )
            else:
                # Otherwise, forward the packet normally
                self.forward_packet(packet, self.paired_adapter.local_classical_router)
        self._send_update(SimulationEventType.DATA_RECEIVED, packet=packet)

    def encrypt_packet(self, packet: ClassicDataPacket):
        encrypted_data = simple_xor_encrypt(packet.data, self.shared_key)
        self.logger.debug(f"Encrypted Data: {packet.data} -> {encrypted_data}")
        
        return ClassicDataPacket(
            data=encrypted_data,
            from_address=packet.from_address,
            to_address=self.paired_adapter.local_classical_router,
            type=packet.type,
            protocol=packet.protocol,
            time=packet.time,
            name=packet.name,
            description=packet.description,
            destination_address=packet.destination_address,
        )

    def decrypt_packet(self, packet: ClassicDataPacket):
        decrypted_data = simple_xor_decrypt(packet.data, self.shared_key)
        self.logger.debug(f"Decrypted Data: {packet.data} -> {decrypted_data}")

        return ClassicDataPacket(
            data=decrypted_data,
            from_address=packet.from_address,
            to_address=packet.destination_address or packet.to_address,
            type=packet.type,
            protocol=packet.protocol,
            time=packet.time,
            name=packet.name,
            description=packet.description,
        )

    def process_packet(self, packet: ClassicDataPacket):
        # Decrypt the packet if a shared key exists
        if self.shared_key:
            packet = self.decrypt_packet(packet)
            # Assuming the decrypted packet is meant to be forwarded to a classical node
            self.forward_packet(
                packet, packet.to_address
            )  # You may need to adjust the logic for determining the next hop
        else:
            print(
                f"Time: {self.network.world.time:.2f}, {self.name} cannot process packet, no shared key"
            )

    def send_classical_data(self, data):

        conn = self.local_classical_router.get_connection(
            self.local_classical_router, self.paired_adapter.local_classical_router
        )

        if not conn:
            raise NotConnectedError(self, self.paired_adapter.local_classical_router)

        packet = QKDTransmissionPacket(
            data=data,
            from_address=self.local_classical_router,
            to_address=self.paired_adapter.local_classical_router,
            type=PacketType.DATA,
        )
        conn.transmit_packet(packet)

    def forward(self):
        self.local_classical_router.forward()

    def intercept_route_packet(self, packet: ClassicDataPacket):
        self.receive_packet(packet)

    def forward_packet(self, packet: ClassicDataPacket, to):
        packet.append_hop(self.local_classical_router)
        # TODO: check why I didn't used router's transmit function instead of re-writing the logic here again.
        direct_connection = self.local_classical_router.get_connection(
            self.local_classical_router, to
        )

        if direct_connection:
            packet.next_hop = packet.to_address
            direct_connection.transmit_packet(packet)
            
            # if (
            #     direct_connection.mtu != -1
            #     and packet.size_bytes > direct_connection.mtu
            # ):
            #     print("Packet size is greater than MTU-------------")
            #     fragments = fragment_packet(packet, direct_connection.mtu)
            #     self._send_update(
            #         SimulationEventType.INFO,
            #         data=dict(
            #             type=InfoEventType.PACKET_FRAGMENTED,
            #             message=f"Packet fragmented into {len(fragments)} fragments because MTU is {direct_connection.mtu} bytes.",
            #         ),
            #     )
            #     for fragment in fragments:
            #         direct_connection.transmit_packet(fragment)
            # else:
            #     direct_connection.transmit_packet(packet)
            return
        
        shortest_path = self.local_classical_router.default_gateway.get_path(self.local_classical_router, packet.to_address)
        
        if len(shortest_path) <= 1:
            raise NotConnectedError(self.local_classical_router, packet.to_address)
        
        next_hop = shortest_path[1]
        
        packet.next_hop = next_hop
        next_connection = self.local_classical_router.get_connection(self.local_classical_router, next_hop)
        
        if not next_connection:
            raise NotConnectedError(self.local_classical_router, next_hop)
        
        if next_connection.mtu != -1 and packet.size_bytes > next_connection.mtu:
            print('Packet size is greater than MTU-------------')
            fragments = fragment_packet(packet, next_connection.mtu)
            self._send_update(SimulationEventType.INFO, data=dict(type=InfoEventType.PACKET_FRAGMENTED, message=f"Packet fragmented into {len(fragments)} fragments because MTU is {next_connection.mtu} bytes."))
            for fragment in fragments:
                next_connection.transmit_packet(fragment)
        else:
            next_connection.transmit_packet(packet)

    def __name__(self):
        return f"QuantumAdapter - '{self.name}'"

    def __repr__(self):
        return self.__name__()
