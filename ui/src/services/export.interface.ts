export interface ExportDataI {
    name: string
    pk?: string
    temporary_world?: boolean
    size: number[]
    zones: ZoneI[]
}

export interface NodeI {
    name: string
    type: string
    address: string
    location: number[]
    parentNetworkName?: string
}

export interface ZoneI {
    name: string
    type: string
    size: number[]
    position: number[]
    networks: NetworkI[]
    adapters: AdapterI[]
}

export interface NetworkI extends NodeI  {
    hosts: HostI[]
    connections: ConnectionI[]
}

export interface HostI extends NodeI {};

export interface ConnectionI {
    from_node: string
    to_node?: string
    length: number
    loss_per_km: number
    noise_model: string
    noise_strength: number
    name: string
    error_rate_threshold?: number
    qbits?: number
    bandwidth: number
    latency: number
    packet_loss_rate?: number;
    packet_error_rate?: number;
    mtu?: number;
    connection_config_preset?: string;
}

export interface AdapterI extends NodeI  {
    quantumHost: string
    classicalHost: string
    classicalNetwork: string
    quantumNetwork: string
}
