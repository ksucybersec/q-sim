"use client"

import { useEffect, useRef, useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NetworkCanvas } from "./components/canvas/network-canvas"
import { Sidebar } from "./components/toolbar/sidebar"
import { TopBar } from "./components/toolbar/top-bar"
import { SimulationControls } from "./components/toolbar/simulation-controls"
import { QuantumStateViewer } from "./components/metrics/quantum-state-viewer"
import { MetricsPanel } from "./components/metrics/metrics-panel"
import { NodeDetailPanel } from "./components/node/node-detail-panel"
import { SimulationTimeline } from "./components/toolbar/simulation-timeline"
import { JSONFormatViewer } from "./components/metrics/json-viewer"
import api from "./services/api"
import { SimulationLogsPanel } from "./components/metrics/simulation-logs"
// import { toast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner"

export default function QuantumNetworkSimulator() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [isSimulationRunning, setIsSimulationRunning] = useState(false)
  const [simulationSpeed, setSimulationSpeed] = useState(1)
  const [currentTime, setCurrentTime] = useState(0)
  const [activeMessages, setActiveMessages] = useState<{ id: string; source: string; target: string; content: any; protocol: string; startTime: number; duration: number }[]>([])

  // Reference to the NetworkCanvas component
  const networkCanvasRef = useRef(null)

  // Update simulation time when running
  useEffect(() => {
    if (!isSimulationRunning) {
      api.getSimulationStatus().then((status) => {
        if(status.is_running) {
          setIsSimulationRunning(true);
        }
      });
      return
    }

    const interval = setInterval(() => {
      setCurrentTime((prevTime) => prevTime + 0.1 * simulationSpeed)
    }, 100)

    return () => clearInterval(interval)
  }, [isSimulationRunning, simulationSpeed])

  // Handle sending a message
  const handleSendMessage = async (source: string, target: string, content: string, protocol: string) => {
    const isSent = await api.sendMessageCommand(source, target, content);

    if (isSent) {

      // Show toast notification
      toast(`Sending ${protocol} message from ${source} to ${target}`);
    } else {
      toast(`Failed sending ${protocol} message from ${source} to ${target}`);
    }

    // Log to console (for debugging)
    console.log(`Sending message: ${source} -> ${target} (${protocol})`, content)
  }

  // Clean up completed messages
  useEffect(() => {
    if (activeMessages.length === 0) return

    const newActiveMessages = activeMessages.filter((msg) => {
      const progress = (currentTime - msg.startTime) / msg.duration
      return progress < 1
    })

    if (newActiveMessages.length !== activeMessages.length) {
      setActiveMessages(newActiveMessages)
    }
  }, [currentTime, activeMessages])

  // Handler for creating nodes from the sidebar
  const handleCreateNode = (actionType: string) => {
    // Get the reference to the network canvas component
    const canvas = networkCanvasRef.current as any
    if (!canvas) return

    // Map action types to the corresponding functions in NetworkCanvas
    const actionMap: any = {
      createClassicalHost: canvas.handleCreateClassicalHost,
      createClassicalRouter: canvas.handleCreateClassicalRouter,
      createQuantumHost: canvas.handleCreateQuantumHost,
      createQuantumAdapter: canvas.handleCreateQuantumAdapter,
      createQuantumRepeater: canvas.handleCreateQuantumRepeater,
      createInternetExchange: canvas.handleCreateInternetExchange,
      createC2QConverter: canvas.handleCreateC2QConverter,
      createQ2CConverter: canvas.handleCreateQ2CConverter,
      createZone: canvas.handleCreateZone,
      createNetwork: canvas.handleCreateNetwork
    }

    // Call the corresponding function if it exists
    if (actionMap[actionType]) {
      actionMap[actionType]()
    } else {
      console.log(`No handler found for action: ${actionType}`)
    }
  }

  const executeSimulation = async () => {
    if (isSimulationRunning) {
      if (!api.stopSimulation())
        return
    } else {
      if (!api.startSimulation())
        return;
    }
    setIsSimulationRunning(!isSimulationRunning);
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 text-slate-50">
      {/* Left Sidebar */}
      <Sidebar onCreateNode={handleCreateNode} />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top Navigation Bar */}
        <TopBar />

        {/* Main Workspace */}
        <div className="flex-1 flex overflow-hidden">
          {/* Network Canvas */}
          <div className="flex-1 relative overflow-hidden">
            <NetworkCanvas
              ref={networkCanvasRef}
              onNodeSelect={(node) => {
                // Find the node in availableNodes
                // const foundNode = availableNodes.find((n) => n.name === node.name)
                setSelectedNode(node)
              }}
              isSimulationRunning={isSimulationRunning}
              simulationTime={currentTime}
              activeMessages={activeMessages}

            />

            {/* Simulation Controls Overlay */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
              <SimulationControls
                isRunning={isSimulationRunning}
                onPlayPause={executeSimulation}
                speed={simulationSpeed}
                onSpeedChange={setSimulationSpeed}
                currentTime={currentTime}
                onTimeChange={setCurrentTime}
              />
            </div>
            <Toaster />
          </div>

          {/* Right Panel - Contextual Information */}
          <div className="w-96 border-l border-slate-700 bg-slate-800 overflow-y-auto">
            <Tabs defaultValue="logs" className="w-full">
              <TabsList className="w-full grid grid-cols-3">
                <TabsTrigger value="logs">Logs</TabsTrigger>
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="json-view">JSON View</TabsTrigger>
              </TabsList>
              <TabsContent value="logs" className="p-4">
                <SimulationLogsPanel />
              </TabsContent>
              <TabsContent value="details" className="p-4">
                <NodeDetailPanel
                  selectedNode={selectedNode}
                  onSendMessage={handleSendMessage}
                  isSimulationRunning={isSimulationRunning}
                />
              </TabsContent>
              {/* <TabsContent value="quantum" className="p-4">
                <QuantumStateViewer selectedNode={selectedNode} />
              </TabsContent> */}
              <TabsContent value="json-view" className="p-4">
                <JSONFormatViewer />
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Timeline at Bottom */}
        {/* <div className="h-24 border-t border-slate-700 bg-slate-800">
          <SimulationTimeline currentTime={currentTime} onTimeChange={setCurrentTime} isRunning={isSimulationRunning} />
        </div> */}
      </div>
    </div>
  )
}

