import threading
import time
from typing import List, Tuple, Union
import uuid

from core.enums import NodeType, ZoneType
from core.network import Network
from core.s_object import Sobject
from utils.encoding import transform_val


class World(Sobject):
    def __init__(
        self,
        size: Tuple[int, int] = (100, 100),
        name="",
        description="",
        *args,
        **kwargs,
    ):
        super().__init__(name, description, *args, **kwargs)
        self.size = size
        self.zones: List[Zone] = []
        self.networks: List[Network] = []  # Store all objects in the world
        self.sequential_stop_flag = False
        self.is_sequential_running = False

    def add_zone(self, zone: "Zone"):
        self.zones.append(zone)

    def add_network(self, network: Network):
        self.networks.append(network)

    def remove_network(self, obj: Network):
        self.networks.remove(obj)

    def is_running(self):
        return all(map(lambda x: x.is_running, self.networks)) or self.is_sequential_running

    def start(self, fps=1.5):
        from classical_network.routing import InternetExchange

        InternetExchange.get_instance().start(fps)

        for network in self.networks:
            network.start(fps)
            

    def start_sequential(self, fps=1.5):
        def _game_loop():
            self.is_sequential_running = True
            from classical_network.routing import InternetExchange

            InternetExchange.get_instance().start(fps)

            while not self.sequential_stop_flag:
                for network in self.networks:
                    # print(f"Forwarding at network {network.name}.")
                    network._forward()
                    time.sleep(fps)
            
            self.sequential_stop_flag = False
            self.is_sequential_running = False
        
        self.logger.info(f"Starting Game Loop - {self.name}")
        thread = threading.Thread(target=_game_loop, daemon=True)
        thread.start()


    def stop(self):
        self.sequential_stop_flag = True
        for network in self.networks:
            network.stop()


class Zone(Sobject):
    def __init__(
        self,
        size: Tuple[int, int],
        position: Tuple[int, int],
        zone_type: ZoneType,
        parent_zone: Union["Zone", "World"] = None,
        name="",
        description="",
    ):
        super().__init__(name, description)
        self.size = size
        self.position = position
        self.zone_type = zone_type
        self.parent_zone = parent_zone
        self.networks: List[Network] = []

        if self.parent_zone and self.parent_zone.on_update_func:
            self.set_on_update_func(self.parent_zone.on_update_func)

    def add_network(self, network: Network):
        self.networks.append(network)

        if self.on_update_func:
            network.on_update_func = self.on_update_func

        if self.parent_zone:
            self.parent_zone.add_network(network)

    def remove_object(self, obj: Network):
        self.objects.remove(obj)

        if self.parent_zone:
            self.parent_zone.remove_network(obj)


class Node(Sobject):

    def __init__(
        self,
        node_type: NodeType,
        location: Tuple[int, int],
        network: Network,
        zone: Zone | World = None,
        name="",
        description="",
        *args,
        **kwargs,
    ):
        super().__init__(name, description)
        self.type = node_type
        self.location = location
        self.network = network
        self.zone = zone
        self.address = (
            None  # Network address can be assigned to both classical and quantum nodes
        )

        with open("log.txt", "a") as f:
            f.write(f"{self.name} created\n")

    def set_on_update_func(self, func):
        self.on_update_func = func

    def forward(self):
        pass

    def on_update(self, event):
        from server.api.simulation.manager import SimulationManager
        # Temporalty
        with open("log.txt", "a") as f:
            f.write(f"{self.name} received event {event.data}\n")

        if self.on_update_func:
            self.on_update_func(event)

        elif SimulationManager.get_instance().is_running:
            SimulationManager.get_instance().on_update(event)


    def to_dict(self):
        dict = {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "location": self.location,
            "network": (
                self.network.name
                if hasattr(self.network, "name")
                else str(self.network)
            ),
            "zone": (
                self.zone.name
                if self.zone and hasattr(self.zone, "name")
                else str(self.zone)
            ),
            "address": self.address,
        }

        return {k: transform_val(v) for k, v in dict.items()}
