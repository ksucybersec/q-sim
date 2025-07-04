"""Zone model for network simulation"""
from typing import List, Tuple, Literal
from pydantic import BaseModel, Field

from data.models.topology.node_model import AdapterModal, NetworkModal

class ZoneModal(BaseModel):
    """Security zone containing networks"""
    name: str = Field(description="Name of the zone")
    type: Literal["SECURE"]= Field(description="Secure/Non-Secure Zone")
    size: Tuple[float, float]= Field(description="Size of the zone world in (x, y) coordinates")
    position: Tuple[float, float]= Field(description="Position of the zone world in (x, y) coordinates")
    networks: List[NetworkModal]= Field(description="List of networks within the zone")
    adapters: List[AdapterModal]= Field(description="List of 'Quantum to Classical adapters' within the zone")

    def get_network_by_name(self, network_name: str) -> NetworkModal:
        """Get a network by its name"""
        for network in self.networks:
            if network.name == network_name:
                return network
        return None
    
    def get_host_by_name(self, host_name: str):
        """Get a host by its name"""
        for network in self.networks:
            for host in network.hosts:
                if host.name == host_name:
                    return host
        return None