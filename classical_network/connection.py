import random
import threading
import time
from typing import Literal, Optional
from classical_network.config.connection_config import ConnectionConfig
from classical_network.node import ClassicalNode
from classical_network.packet import ClassicDataPacket
from classical_network.presets.connection_presets import DEFAULT_PRESET
from core.base_classes import Sobject
from core.enums import SimulationEventType
from core.exceptions import ConnectionDownError, MtuExceededError, RoutingError


class ClassicConnection(Sobject):
    def __init__(
        self,
        node_1: "ClassicalNode",
        node_2: "ClassicalNode",
        config: ConnectionConfig,
        status: Literal["up", "down"] = "up",
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        _name = (
            name
            if name is not None
            else f"{config.name_prefix}_{node_1.name}_{node_2.name}"
        )
        _description = description if description is not None else config.description
        super().__init__(_name, _description)

        self.node_1 = node_1
        self.node_2 = node_2
        self.bandwidth = (
            DEFAULT_PRESET.bandwidth if config.bandwidth == -1 else config.bandwidth
        )
        self.latency = (
            DEFAULT_PRESET.latency if config.latency == -1 else config.latency
        )
        self.packet_loss_rate = (
            DEFAULT_PRESET.packet_error_rate
            if config.packet_loss_rate == -1
            else config.packet_loss_rate
        )
        self.packet_error_rate = (
            DEFAULT_PRESET.packet_error_rate
            if config.packet_error_rate == -1
            else config.packet_error_rate
        )
        self.mtu = DEFAULT_PRESET.mtu if config.mtu == -1 else config.mtu
        self.status = status

        if not (0.0 <= self.packet_loss_rate <= 1.0):
            raise ValueError("Packet loss rate must be between 0.0 and 1.0.")
        self.packet_loss_rate = float(self.packet_loss_rate)

        if not (0.0 <= self.packet_error_rate <= 1.0):
            raise ValueError("Packet error rate must be between 0.0 and 1.0.")
        self.packet_error_rate = float(self.packet_error_rate)

        if self.mtu <= 0:
            raise ValueError("MTU must be a positive integer.")
        self.mtu = int(self.mtu)

    def __name__(self):
        return f"{self.node_1.name} <-> {self.node_2.name}"

    def __repr__(self):
        return self.__name__()

    def debug_print(self, log):
        return
        print(log)

    def _async_transmit_worker(
        self,
        packet: "ClassicDataPacket",
        origin_node: "ClassicalNode",
        destination_on_link: "ClassicalNode",
        total_simulated_delay: float,
    ):
        """
        Worker function executed in a separate thread to simulate the
        in-flight part of packet transmission (loss, error, delay, delivery).
        """
        thread_name = threading.current_thread().name
        self.debug_print(
            f"[{thread_name}] Async transmission started for packet id {packet.id} "
            f"to {destination_on_link.name}."
        )

        try:
            if random.random() < self.packet_loss_rate:
                self._send_update(
                    SimulationEventType.PACKET_LOTS,
                    packet_id=packet.id,
                    connection_name=self.name,
                    loss_rate=self.packet_loss_rate,
                )
                return

            if random.random() < self.packet_error_rate:
                self._send_update(
                    SimulationEventType.PACKET_CORRUPTED,
                    packet_id=packet.id,
                    error_rate=self.packet_error_rate,
                    connection_name=self.name,
                )

            time.sleep(total_simulated_delay)

            destination_on_link.write_buffer(origin_node, packet)

            self._send_update(
                SimulationEventType.PACKET_DELIVERED,
                packet_id=packet.id,
                destination=destination_on_link.name,
                delay=total_simulated_delay,
            )
        except Exception as e:
            self.debug_print(
                f"[{thread_name}] Unexpected error during async transmission of packet id {packet.id} on '{self.name}': {e}"
            )
            self._send_update(
                SimulationEventType.TRANSMISSION_FAILED,
                packet_id=packet.id,
                error=str(e),
            )

    def transmit_packet(self, packet: "ClassicDataPacket"):
        origin_node = packet.hops[-1]
        destination_on_link = None
        if origin_node == self.node_1 and packet.next_hop == self.node_2:
            destination_on_link = self.node_2
        elif origin_node == self.node_2 and packet.next_hop == self.node_1:
            destination_on_link = self.node_1
        else:
            log_msg = (
                f"Sync Check on '{self.name}': Routing/Call Error. "
                f"Origin: {origin_node.name if origin_node else 'None'}, "
                f"Packet Next Hop: {packet.next_hop.name if packet.next_hop else 'None'}. "
                f"Nodes on connection: {self.node_1.name}, {self.node_2.name}. "
                f"Packet id {packet.id} cannot be routed."
            )
            self.debug_print(log_msg)
            self._send_update(
                SimulationEventType.ROUTING_ERROR,
                packet_id=packet.id,
                reason="invalid_next_hop",
            )
            raise RoutingError(log_msg)

        self.debug_print(
            f"Sync Check on '{self.name}': {origin_node.name} attempting to transmit packet id {packet.id} to {destination_on_link.name}."
        )

        if self.status != "up":
            msg = f"Sync Check on '{self.name}': Link is DOWN. Packet id {packet.id} cannot be transmitted."
            self.debug_print(msg)
            self._send_update(
                SimulationEventType.PACKET_DROPPED,
                packet_id=packet.id,
                reason="link_down",
            )
            raise ConnectionDownError(msg)

        if self.mtu != -1 and packet.size_bytes > self.mtu:
            self._send_update(
                SimulationEventType.PACKET_DROPPED,
                packet_id=packet.id,
                reason="mtu_exceeded",
                packet_size=packet.size_bytes,
                mtu=self.mtu,
            )
            raise MtuExceededError(packet.id, packet.size_bytes, self.mtu, self.name)

        # Calculate Delays
        if self.bandwidth <= 0:
            msg = f"Sync Check on '{self.name}': Bandwidth is zero or negative. Packet id {packet.id} transmission impossible."
            self.debug_print(msg)
            raise ValueError(msg)  # Or a more specific bandwidth error
        transmission_delay = packet.size_bits / self.bandwidth
        total_simulated_delay = self.latency + transmission_delay

        self.debug_print(
            f"Sync Check on '{self.name}': Packet id {packet.id} passed initial checks. "
            f"Calculated total delay: {total_simulated_delay:.6f}s. Launching async transmission."
        )
        self._send_update(
            SimulationEventType.TRANSMISSION_STARTED,
            packet_id=packet.id,
            delay=total_simulated_delay,
            bandwidth=self.bandwidth,
        )

        thread_args = (
            packet,
            origin_node,
            destination_on_link,
            total_simulated_delay,
        )

        transmission_thread = threading.Thread(
            target=self._async_transmit_worker,
            args=thread_args,
            name=f"TransmitThread-Conn_{self.name}-Pkt_{packet.id}",
            daemon=True,
        )
        transmission_thread.daemon = True
        transmission_thread.start()
