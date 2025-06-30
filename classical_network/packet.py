from datetime import datetime
from collections import defaultdict
from typing import Any
import uuid
from classical_network.enum import PacketType
from core.base_classes import Node, Sobject


class ClassicDataPacket(Sobject):
    def __init__(
        self,
        data: Any,
        from_address: Node,
        to_address: Node,
        type: PacketType,
        protocol="tcp",
        time=0,
        name="",
        description="",
        destination_address: Node = None,
    ):
        super().__init__(name, description)

        if time == 0:
            time = datetime.now().timestamp

        self.id = uuid.uuid4().hex
        self.from_address = from_address
        self.to_address = to_address
        self.type = type
        self.time = time
        self.hops = [from_address]
        self.protocol = protocol
        self.next_hop = to_address
        self.data = data
        self.destination_address = destination_address
        self.headers = defaultdict(list)

    def append_hop(self, hop: Node):
        self.hops.append(hop)

    def append_header(self, header:str, value: Any):
        self.headers[header].append(value)

    def get_header(self, header: str) -> Any:
        return self.headers[header][0] if header in self.headers else None
    
    def remove_header(self, header: str, value: Any = None):
        if value is not None:
            if value in self.headers[header]:
                self.headers[header].remove(value)
        else:
            del self.headers[header]

    def to_dict(self):
        dict_str = {
            'type': str(type(self)),
            'from': self.from_address.name,
            'to': self.to_address.name,
            'hops': list(map(lambda x : x.name,self.hops)),
            'data': str(self.data),
            'destination_address': self.destination_address.name if self.destination_address else None,
            'headers': self.headers
        }
        
        return dict_str
    
    @property
    def size_bytes(self):
        # Check if fragmented packet has size override
        header_size = self.get_header('size_bytes')
        if header_size:
            return header_size
        
        # Original packet size calculation
        return len(self.data) + 20  # data + IP header
    
    @property
    def size_bits(self):
        return self.size_bytes * 8