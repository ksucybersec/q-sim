export interface TransmiTPacketI {
    event_type: string
    node: string
    timestamp: number
    data: PacketData
  }
  
  export interface PacketData {
    packet: Packet
  }
  
  export interface Packet {
    type: string
    from: string
    to: string
    hops: string[]
    data: string
    destination_address: string
  }
  
  export interface RealtimeLogSummaryI {
    summary_text: string[]
    cited_log_entries: Object[]
    error_message: string
    thought_process: string
  }