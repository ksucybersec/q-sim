from copy import copy
from typing import List
from classical_network.packet import ClassicDataPacket


def fragment_packet(packet: ClassicDataPacket, mtu: int, original_packet_id=None):
    """Fragment a packet based on MTU"""
    if packet.size_bytes <= mtu:
        return [packet]
    
    fragments = []
    data_size = len(packet.data)
    fragment_size = mtu - 20  # IP header overhead
    fragment_id = original_packet_id or packet.id
    
    offset = 0
    while offset < data_size:
        remaining = data_size - offset
        current_size = min(fragment_size, remaining)
        print(f"Remaining: {remaining}, Fragment size: {current_size}, Data size: {data_size}, offset: {offset}")
        is_last = (offset + current_size) >= data_size
        
        # Create fragment with fragmentation headers
        fragment = copy(packet)
        
        # Add fragmentation fields
        fragment.append_header('fragment_id', fragment_id)
        fragment.append_header('fragment_offset', offset)
        fragment.append_header('more_fragments', not is_last)
        fragment.append_header('size_bytes', current_size + 20)
        fragment.data = packet.data[offset:offset+current_size],
        
        fragments.append(fragment)
        offset += current_size
    
    return fragments

def reassemble_fragments(fragments: List[ClassicDataPacket]):
    """Reassemble fragments into original packet"""
    if not fragments:
        return None
    
    # Sort by offset
    fragments.sort(key=lambda f: f.get_header('fragment_offset'))
    
    # Check if all fragments present
    expected_offset = 0
    for frag in fragments:
        if frag.get_header('fragment_offset') != expected_offset:
            return None  # Missing fragment
        expected_offset += len(frag.data)
    
    # Check last fragment
    if fragments[-1].get_header('more_fragments'):
        return None  # Missing final fragment
    
    # Reassemble data
    reassembled_data = b''.join(frag.data for frag in fragments)
    
    # Create reassembled packet
    original = fragments[0]
    reassembled = copy(original)
    reassembled.data = reassembled_data
    reassembled.remove_header('fragment_offset')
    reassembled.remove_header('more_fragments')
    reassembled.remove_header('fragment_id')
    reassembled.remove_header('size_bytes')

    reassembled.append_header('reassembly_complete', True)

    return reassembled
