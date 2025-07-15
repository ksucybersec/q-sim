"use client"

import { useEffect, useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { Cpu, Unplug, EthernetPort } from "lucide-react"
import { MessagingPanel } from "../metrics/messaging-panel"
import { ClassicalHost } from "./classical/classicalHost"
import { SimulatorNode } from "./base/baseNode"
import { NetworkManager } from "./network/networkManager"
import { SimulatorConnection } from "./connections/line"
import { ConnectionManager } from "./connections/connectionManager"
import { cloneDeep } from "lodash"
import { NodeFamily, SimulationNodeType } from "./base/enums"
import { ConnectionConfigPreset } from "@/services/apiResponse.interface"
import api from "@/services/api"
import { Button } from "../ui/button"
import { sendComponentDisconnectedEvent } from "@/helpers/userEvents/userEvents"

interface NodeDetailPanelProps {
  selectedNode: SimulatorNode | null
  updateNodeProperties?: (properties: Partial<SimulatorNode>) => void
  onSendMessage?: (source: string, target: string, message: string, protocol: string) => void
  isSimulationRunning?: boolean
}

export function NodeDetailPanel({
  selectedNode,
  updateNodeProperties = () => { },
  onSendMessage = () => { },
  isSimulationRunning = false,
}: NodeDetailPanelProps) {
  const [activeTab, setActiveTab] = useState("properties")
  const [isHost, setIsHost] = useState(false)
  const [connections, setConnections] = useState<SimulatorConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<SimulatorConnection | null>(null);
  const [changeDetection, setChangeDetection] = useState(0);
  const [connectionConfigPresets, setConnectionConfigPresets] = useState<ConnectionConfigPreset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('none')


  const forceDetectChange = () => {
    // This is a workaround to force re-render the component when needed (Hackish)
    setChangeDetection(prev => prev + 1);
  }

  useEffect(() => {
    ConnectionManager.getInstance()?.onConnectionCallback(updateConnections);

    api.getConnectionPresets().then(presets => {
      if (!presets?.length) {
        console.error("Failed to fetch connection presets", presets);
        return;
      }
      setConnectionConfigPresets(presets);
    });
  }, [])

  useEffect(() => {
    setIsHost(selectedNode instanceof ClassicalHost);
    updateConnections();
  }, [selectedNode])

  const updateConnections = (...args: any[]) => {
    const connectionManager = ConnectionManager.getInstance();
    if (connectionManager) {
      setConnections(connectionManager.getAllConnections().filter((c) => c.metaData.from === selectedNode || c.metaData.to === selectedNode));
    }
  };

  if (!selectedNode) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <p className="text-slate-400">Select a node to view its details</p>
      </div>
    )
  }

  const disconnectConnection = () => {
    const connectionManager = ConnectionManager.getInstance();
    if (connectionManager && selectedConnection) {
      connectionManager.removeLine(selectedConnection)
      sendComponentDisconnectedEvent(selectedConnection.metaData.from.name, selectedConnection.metaData.to?.name as string)
    }
  }

  const onNameChange = (event: any) => {
    let newName = event.target.value;
    const isDuplicate = NetworkManager.getInstance().canvas.getObjects().filter(x => x instanceof SimulatorNode).some(x => x.name === newName);
    if (isDuplicate) {
      // toast('Name Already Used');
      alert('Name Already Used');
      newName += (" Copy" + Math.floor(Math.random() * 1000)); // Append a random number to make it unique
    }
    selectedNode.name = newName;
  }

  const onConnectionPresetChanged = (presetName: string) => {
    const presetConfig = connectionConfigPresets.find((preset) => preset.preset_name === presetName)?.preset_config;
    if (!presetConfig) return;

    if (selectedConnection) {
      const updatedConnection = cloneDeep(selectedConnection);
      if (updatedConnection) {
        updatedConnection.metaData.bandwidth = presetConfig.bandwidth / 1e6;
        updatedConnection.metaData.latency = presetConfig.latency;
        updatedConnection.metaData.packet_loss_rate = presetConfig.packet_loss_rate;
        updatedConnection.metaData.packet_error_rate = presetConfig.packet_error_rate;
        updatedConnection.metaData.mtu = presetConfig.mtu;
        updatedConnection.metaData.connection_config_preset = presetName;

        const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
        if (connection) {
          connection.metaData.bandwidth = presetConfig.bandwidth / 1e6;
          connection.metaData.latency = presetConfig.latency;
          updatedConnection.metaData.packet_loss_rate = presetConfig.packet_loss_rate;
          connection.metaData.packet_error_rate = presetConfig.packet_error_rate;
          connection.metaData.mtu = presetConfig.mtu;
          connection.metaData.connection_config_preset = presetName;
        }
        setSelectedConnection(updatedConnection);
        setSelectedPreset(presetName);
      }
    }
  };

  const findConnection = (fromNode: SimulatorNode, toNodeName: string) => {
    return connections.find(conn => conn.metaData.from === fromNode && conn.metaData.to?.name === toNodeName) || connections.find(conn => conn.metaData.to === fromNode && conn.metaData.from?.name === toNodeName) || null;
  }

  const onLossPerKmChange = (valueArray: (number | string)[]) => {
    const newLossPerKm = +valueArray[0];

    setSelectedConnection((prev) => {
      if (!prev) return null;
      const updatedConnection = cloneDeep(prev);
      updatedConnection.metaData.lossPerKm = newLossPerKm;

      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) connection.metaData.lossPerKm = newLossPerKm;
      return updatedConnection;
    })
  }

  const onBandwidthChange = (valueArray: (number | string)[]) => {
    const newBandwidth = +valueArray[0];
    setSelectedConnection((prev) => {
      if (!prev) return null;
      const updatedConnection = cloneDeep(prev);
      updatedConnection.metaData.bandwidth = newBandwidth;

      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) connection.metaData.bandwidth = newBandwidth;
      return updatedConnection;
    })
  }

  const onLatencyChange = (event: any) => {
    const newLatency = +event.target.value;
    setSelectedConnection((prev) => {
      if (!prev) return null;
      const updatedConnection = cloneDeep(prev);
      updatedConnection.metaData.latency = newLatency;
      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) connection.metaData.latency = newLatency;
      return updatedConnection;
    })
  }

  const onMTUChange = (event: any) => {
    const newMTU = +event.target.value;
    setSelectedConnection((prev) => {
      if (!prev) return null;
      const updatedConnection = cloneDeep(prev);
      updatedConnection.metaData.mtu = newMTU;
      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) connection.metaData.mtu = newMTU;
      return updatedConnection;
    })
  }

  const onPacketLossRateChange = (valueArray: (number | string)[]) => {
    const newPacketLossRate = +valueArray[0];
    setSelectedConnection((prev) => {
      if (!prev) return null;
      const updatedConnection = cloneDeep(prev);
      updatedConnection.metaData.packet_loss_rate = newPacketLossRate;
      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) connection.metaData.packet_loss_rate = newPacketLossRate;
      return updatedConnection;
    })
  }

  const onPacketErrorRateChange = (valueArray: (number | string)[]) => {
    const newPacketErrorRate = +valueArray[0];
    setSelectedConnection((prev) => {
      if (!prev) return null;
      const updatedConnection = cloneDeep(prev);
      updatedConnection.metaData.packet_error_rate = newPacketErrorRate;
      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) connection.metaData.packet_error_rate = newPacketErrorRate;
      return updatedConnection;
    })
  }

  const onErrorRateChange = (valueArray: (number | string)[]) => {
    const newErrorRate = +valueArray[0];
    if (selectedConnection) {
      selectedConnection.metaData.error_rate_threshold = newErrorRate;

      const connection = findConnection(selectedNode, (selectedNode.name === selectedConnection.metaData.to?.name ? selectedConnection.metaData.from?.name : selectedConnection.metaData.to?.name) || '');
      if (connection) {
        connection.metaData.error_rate_threshold = newErrorRate;
      }
      forceDetectChange();
    }
  }

  const onQbitsChange = (valueArray: (number | string)[]) => {
    const inputValue = +valueArray[0];

    // Find nearest power of 2 (minimum 8)
    const nearestPowerOf2 = Math.max(8, Math.pow(2, Math.round(Math.log2(inputValue))));

    if (selectedConnection) {
      selectedConnection.metaData.qbits = nearestPowerOf2;

      const connection = findConnection(selectedNode, (selectedNode.name === selectedConnection.metaData.to?.name ? selectedConnection.metaData.from?.name : selectedConnection.metaData.to?.name) || '');
      if (connection) {
        connection.metaData.qbits = nearestPowerOf2;
      }

      forceDetectChange();
    }
  }

  const onNoiseModelChange = (value: string) => {
    if (selectedConnection) {
      const updatedConnection = cloneDeep(selectedConnection);
      updatedConnection.metaData.noise_model = value;
      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) {
        connection.metaData.noise_model = value;
      }
      setSelectedConnection(updatedConnection);
    }
  }

  const onNoiseStrengthChange = (valueArray: (number | string)[]) => {
    const newNoiseStrength = +valueArray[0];
    if (selectedConnection) {
      const updatedConnection = cloneDeep(selectedConnection);
      updatedConnection.metaData.noise_strength = newNoiseStrength;

      const connection = findConnection(selectedNode, (selectedNode.name === updatedConnection.metaData.to?.name ? updatedConnection.metaData.from?.name : updatedConnection.metaData.to?.name) || '');
      if (connection) {
        connection.metaData.noise_strength = newNoiseStrength;
      }
      setSelectedConnection(updatedConnection);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-md bg-green-500">
          <Cpu className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-lg font-medium">{selectedNode.name}</h3>
          <p className="text-sm text-slate-400">Quantum Host</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-4">
          <TabsTrigger value="properties">Properties</TabsTrigger>
          {/* <TabsTrigger value="behavior">Behavior</TabsTrigger> */}
          {/* <TabsTrigger value="code">Code</TabsTrigger> */}
          {isHost && <TabsTrigger value="messaging">Messaging</TabsTrigger>}
        </TabsList>

        <TabsContent value="properties" className="space-y-4 pt-4">
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="node-name">Name</Label>
              <Input id="node-name" defaultValue={selectedNode.name} onChange={onNameChange} />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="node-type">Type</Label>
              <span className="hidden">{selectedNode?.nodeType?.toString() || 'N/A'}</span>
              <Select defaultValue="-1" disabled value={selectedNode?.nodeType?.toString()}>
                <SelectTrigger id="node-type">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={SimulationNodeType.QUANTUM_HOST.toString()}>Quantum Host</SelectItem>
                  <SelectItem value={SimulationNodeType.QUANTUM_ADAPTER.toString()}>Quantum Adapter</SelectItem>
                  <SelectItem value={SimulationNodeType.CLASSICAL_HOST.toString()}>Classical Host</SelectItem>
                  <SelectItem value={SimulationNodeType.CLASSICAL_ROUTER.toString()}>Classical Router</SelectItem>
                  <SelectItem value="-1">Unknown</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Separator />

            {/* <div className="flex items-center gap-3">
              <Settings className="h-5 w-5 text-slate-400" />
              <h3 className="text-lg font-medium">Host Settings</h3>
            </div> */}

            <Separator />

            <div className="flex items-center gap-3">
              <EthernetPort className="h-5 w-5 text-slate-400" />
              <h3 className="text-lg font-medium">Connection Settings</h3>
            </div>

            <div className=" flex justify-between items-center">

              <div className="grid gap-2">
                <Label htmlFor="node-type">Connection From</Label>
                <Select
                  disabled={connections.length === 0}
                  defaultValue={connections.length > 0 ? (connections[0].metaData.from === selectedNode ? connections[0].metaData.to?.name : connections[0].metaData.from?.name) : 'na'}
                  onValueChange={(value) => {
                    const connection = findConnection(selectedNode, value);
                    setSelectedConnection(connection || null);
                    setSelectedPreset(connection?.metaData.connection_config_preset || 'none');
                  }}
                >
                  <SelectTrigger id="node-type">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="na">N/A</SelectItem>
                    {
                      connections.map(conn => {
                        const otherNode = conn.metaData.from === selectedNode ? conn.metaData.to : conn.metaData.from;
                        if (!otherNode) {
                          return null;
                        }
                        return <SelectItem key={otherNode?.name} value={otherNode?.name}>{otherNode.name}</SelectItem>
                      })
                    }
                  </SelectContent>
                </Select>

              </div>
              {selectedConnection && (
                <Button variant="destructive" onClick={disconnectConnection}>
                  <Unplug></Unplug>
                  Disconnect
                </Button>)}
            </div>

            {
              selectedConnection ?
                <div className="grid gap-2">
                  <Label htmlFor="losskm">Loss Per Kilometer</Label>
                  <div className="flex items-center gap-4">
                    <Slider disabled={selectedConnection.metaData.connectionType === NodeFamily.QUANTUM && selectedConnection.metaData.noise_model === 'none'}
                      id="losskm"
                      value={[selectedConnection.metaData.lossPerKm || 0.0001]}
                      max={1}
                      min={0.0001}
                      step={0.0005}
                      className="flex-1"
                      onValueChange={onLossPerKmChange}
                    />
                    <span className="w-18 text-center">{((selectedConnection.metaData.lossPerKm || 0.0001) * 100).toFixed(2)}%/km</span>
                  </div>
                </div>
                : 'Select Connection'
            }


            {selectedConnection?.metaData.connectionType === NodeFamily.CLASSICAL ?

              <span>

                <div className="grid gap-2">
                  <Label htmlFor="node-type">Connection Preset</Label>
                  <Select value={selectedConnection?.metaData.connection_config_preset || 'none'} onValueChange={onConnectionPresetChanged}>
                    <SelectTrigger id="node-type" className="max-w-full overflow-hidden text-ellipsis">
                      <SelectValue placeholder="Select Connection Preset" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Custom Settings</SelectItem>
                      {
                        connectionConfigPresets.map((preset, index) => (
                          <SelectItem value={preset.preset_name} key={index}>
                            {preset.preset_config.description}
                          </SelectItem>
                        ))
                      }
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="bandwidth">Bandwidth</Label>
                  <div className="flex items-center gap-4">
                    <Slider disabled={selectedPreset !== 'none'}
                      id="bandwidth"
                      value={[selectedConnection.metaData.bandwidth || 10]}
                      max={1024}
                      min={1}
                      step={1}
                      className="flex-1"
                      onValueChange={onBandwidthChange}
                    />
                    <span className="w-18 text-center">{((selectedConnection.metaData.bandwidth || 10))} Mbps</span>
                  </div>

                </div>

                <div className="grid gap-2">
                  <div className="grid gap-2">
                    <Label htmlFor="node-name">Latency</Label>
                    <Input id="node-name" type="number" value={selectedConnection.metaData.latency || -1} disabled={selectedPreset !== 'none'} onChange={onLatencyChange} />
                  </div>
                </div>


                <div className="grid gap-2">
                  <Label htmlFor="bandwidth">Packet Loss Probability</Label>
                  <div className="flex items-center gap-4">
                    <Slider
                      id="bandwidth" disabled={selectedPreset !== 'none'}
                      value={[selectedConnection.metaData.packet_loss_rate || 0.1]}
                      max={1}
                      min={0.01}
                      step={0.01}
                      className="flex-1"
                      onValueChange={onPacketLossRateChange}
                    />
                    <span className="w-18 text-center">{((selectedConnection.metaData.packet_loss_rate || 0.1) * 100).toFixed(2)}%</span>
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="bandwidth">Packet Error Probability</Label>
                  <div className="flex items-center gap-4">
                    <Slider
                      id="bandwidth" disabled={selectedPreset !== 'none'}
                      value={[selectedConnection.metaData.packet_error_rate || 0.1]}
                      max={1}
                      min={0.01}
                      step={0.01}
                      className="flex-1"
                      onValueChange={onPacketErrorRateChange}
                    />
                    <span className="w-18 text-center">{((selectedConnection.metaData.packet_error_rate || 0.1) * 100).toFixed(2)}%</span>
                  </div>

                </div>
                <div className="grid gap-2">
                  <div className="grid gap-2">
                    <Label htmlFor="node-name">MTU</Label>
                    <Input id="node-name" type="number" disabled={selectedPreset !== 'none'} value={selectedConnection.metaData.mtu || -1} onChange={onMTUChange} />
                  </div>
                </div>
              </span>

              : null
            }

            {
              selectedConnection?.metaData.connectionType === NodeFamily.QUANTUM ?

                <span>

                  <div className="grid gap-2 ">
                    <Label htmlFor="noise-model">Noise Model</Label>
                    <Select defaultValue={selectedConnection.metaData.noise_model || 'none'} onValueChange={onNoiseModelChange}>
                      <SelectTrigger id="noise-model" className="w-full">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="transmutation">Transmutation</SelectItem>
                        <SelectItem value="depolarizing">Depolarizing</SelectItem>
                        <SelectItem value="amplitude_damping">Amplitude Damping</SelectItem>
                        <SelectItem value="phase_damping">Phase Damping</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="noise-strength">Noise Strength</Label>
                    <div className="flex items-center gap-4">
                      <Slider
                        id="noise-strength"
                        value={[selectedConnection.metaData.noise_strength || 0.01]}
                        max={1}
                        min={0.01}
                        step={0.05}
                        className="flex-1"
                        onValueChange={onNoiseStrengthChange}
                      />
                      <span className="w-8 text-center">{((selectedConnection.metaData.noise_strength || 0.01) * 100).toFixed(0)}%</span>
                    </div>
                  </div>


                  <div className="grid gap-2">
                    <Label htmlFor="error-rate">Error Rate (%)</Label>
                    <div className="flex items-center gap-4">
                      <Slider
                        id="error-rate"
                        value={[selectedConnection?.metaData.error_rate_threshold || 0]}
                        max={100}
                        min={1}
                        step={1}
                        className="flex-1"
                        onValueChange={onErrorRateChange}
                      />
                      <span className="w-12 text-center">{selectedConnection?.metaData.error_rate_threshold || 0}%</span>
                    </div>
                  </div>


                  <div className="grid gap-2">
                    <Label htmlFor="qbits">Qbits</Label>
                    <div className="flex items-center gap-4">
                      <Slider
                        id="qbits"
                        value={[selectedConnection?.metaData.qbits || 16]}
                        max={1024}
                        min={16}
                        step={8}
                        className="flex-1"
                        onValueChange={onQbitsChange}
                      />
                      <span className="w-12 text-center">{selectedConnection?.metaData.qbits || 16}</span>
                    </div>
                  </div>
                </span>

                : null
            }

            {/* <div className="grid gap-2">
              <Label htmlFor="coherence-time">Coherence Time (μs)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  id="coherence-time"
                  defaultValue={[1]}
                  max={500}
                  min={10}
                  step={10}
                  className="flex-1"
                />
                <span className="w-12 text-center">{1}</span>
              </div>
            </div> */}

            {/* <div className="grid gap-2">
              <Label htmlFor="protocol">Quantum Protocol</Label>
              <Select defaultValue={'BB84'}>
                <SelectTrigger id="protocol">
                  <SelectValue placeholder="Select protocol" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BB84">BB84</SelectItem>
                  <SelectItem value="E91">E91</SelectItem>
                  <SelectItem value="B92">B92</SelectItem>
                  <SelectItem value="CUSTOM">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div> */}
          </div>
        </TabsContent>

        {/* <TabsContent value="behavior" className="space-y-4 pt-4">
          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-slate-400" />
                <Label htmlFor="decoherence">Simulate Decoherence</Label>
              </div>
              <Switch id="decoherence" defaultChecked />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-slate-400" />
                <Label htmlFor="gate-errors">Gate Errors</Label>
              </div>
              <Switch id="gate-errors" defaultChecked />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-slate-400" />
                <Label htmlFor="measurement-errors">Measurement Errors</Label>
              </div>
              <Switch id="measurement-errors" defaultChecked />
            </div>

            <Separator />

            <div className="grid gap-2">
              <Label htmlFor="behavior-model">Behavior Model</Label>
              <Select defaultValue="realistic">
                <SelectTrigger id="behavior-model">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ideal">Ideal (No Errors)</SelectItem>
                  <SelectItem value="simplified">Simplified</SelectItem>
                  <SelectItem value="realistic">Realistic</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="environment">Environment</Label>
              <Select defaultValue="room-temp">
                <SelectTrigger id="environment">
                  <SelectValue placeholder="Select environment" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="room-temp">Room Temperature</SelectItem>
                  <SelectItem value="cryogenic">Cryogenic</SelectItem>
                  <SelectItem value="vacuum">Vacuum</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </TabsContent> */}

        {/* <TabsContent value="code" className="pt-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="code-editor">Custom Behavior Code</Label>
              <Button variant="outline" size="sm">
                <Code className="h-4 w-4 mr-2" />
                Validate
              </Button>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-slate-900 rounded-md p-4 font-mono text-sm overflow-auto">
                <pre className="text-green-400">
                  {`// Quantum Host behavior
                    function initializeNode() {
                    // Initialize qubits in |0⟩ state
                    for (let i = 0; i < this.qubits; i++) {
                      this.initQubit(i);
                    }

                    // Apply Hadamard to create superposition
                    this.applyGate("H", 0);

                    // Setup entanglement with target
                    if (this.connections.length > 0) {
                      this.entangle(0, this.connections[0], 0);
                    }
                  }`}
                </pre>
              </div>
              <div className="h-64"></div>
            </div>
          </div>
        </TabsContent> */}

        {isHost && (
          <TabsContent value="messaging" className="pt-4">
            <MessagingPanel
              selectedNode={selectedNode}
              onSendMessage={onSendMessage}
              isSimulationRunning={isSimulationRunning}
            />
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}

