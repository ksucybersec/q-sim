import { ExportDataI } from "./export.interface"

export interface StartSimulationResponse {
    pk: string
    name: string
    world_id: string
    status: string
    start_time: string
    last_updated: string
    end_time: any
    configuration: ExportDataI
    metrics: any
}

export interface ConnectionConfigPreset {
  preset_name: string
  preset_config: PresetConfig
}

export interface PresetConfig {
  bandwidth: number
  latency: number
  packet_loss_rate: number
  packet_error_rate: number
  mtu: number
  name_prefix: string
  description: string
}
