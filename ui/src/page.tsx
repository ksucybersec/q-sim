"use client"

import { useEffect, useRef, useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NetworkCanvas } from "./components/canvas/network-canvas"
import { Sidebar } from "./components/toolbar/sidebar"
import { TopBar } from "./components/toolbar/top-bar"
import { SimulationControls } from "./components/toolbar/simulation-controls"
import { NodeDetailPanel } from "./components/node/node-detail-panel"
import { JSONFormatViewer } from "./components/metrics/json-viewer"
import api from "./services/api"
import { SimulationLogsPanel } from "./components/metrics/simulation-logs"
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner"
import { ActiveLabIndicator } from "./components/labs/active-lab-indicator"
import { ExerciseI } from "./components/labs/exercise /exercise"
import { EXERCISES } from "./components/labs/exercise "
import { ConnectionManager } from "./components/node/connections/connectionManager"
import { AIAgentsModal } from "./components/ai-agents/ai-agents-modal"
import simulationState from "./helpers/utils/simulationState"
import { SimulatorNode } from "./components/node/base/baseNode"
import { RealtimeLogSummary } from "./components/metrics/realtime-log-summary"
import { ClassicalHost } from "./components/node/classical/classicalHost"
import { MessagingPanel } from "./components/metrics/messaging-panel"

type TabIDs = 'logs' | 'details' | 'messages' | 'json-view' | string

export default function QuantumNetworkSimulator() {
  const [selectedNode, setSelectedNode] = useState<SimulatorNode | null>(null)
  const [isSimulationRunning, setIsSimulationRunning] = useState(false)
  const [simulationSpeed, setSimulationSpeed] = useState(1)
  const [currentTime, setCurrentTime] = useState(0)
  const [simulationStateUpdateCount, setSimulationStateUpdateCount] = useState(0)
  const [activeLabObject, setActiveLabObject] = useState<ExerciseI | null>(null)
  const [activeMessages, setActiveMessages] = useState<{ id: string; source: string; target: string; content: any; protocol: string; startTime: number; duration: number }[]>([])
  const [activeTab, setActiveTab] = useState<TabIDs>("logs")
  // const [activeTopologyID, setActiveTopologyID] = useState<string | null>(null)

  // Lab-related state
  const [activeLab, setActiveLab] = useState<string | null>(null)
  const [labProgress, setLabProgress] = useState(0)
  const [completedLabs, setCompletedLabs] = useState<string[]>([])

  // State variable for the AI panel
  const [isAIPanelOpen, setIsAIPanelOpen] = useState(false)

  // Reference to the NetworkCanvas component
  const networkCanvasRef = useRef(null)

  const [isLogSummaryMinimized, setIsLogSummaryMinimized] = useState(false)

  useEffect(() => {
    setTimeout(() => {
      registerConnectionCallback();
    }, 5000);
  }, []);

  // Update simulation time when running
  useEffect(() => {
    triggerLabCheck();
    if (!isSimulationRunning) {
      api.getSimulationStatus().then((status) => {
        if (status.is_running) {
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
    triggerLabCheck();
  }

  const onSelectedNodeChanged = (node: SimulatorNode) => {
    setSelectedNode(node)
    setActiveTab('logs')
  }

  useEffect(() => {
    if (activeTab === 'messages' && !(selectedNode instanceof ClassicalHost)) {
      setActiveTab('logs');
    } else if (selectedNode instanceof ClassicalHost) {
      setActiveTab('messages');
    }
  }, [selectedNode]);

  const triggerLabCheck = () => {
    setActiveLab((currentActiveLab) => {
      if (!currentActiveLab) return currentActiveLab;

      setSimulationStateUpdateCount((prev) => prev + 1);

      return currentActiveLab;
    });
  }

  const registerConnectionCallback = () => {
    try {
      ConnectionManager.getInstance().onConnectionCallback((conn, from, to) => {
        triggerLabCheck();
      });
    } catch (error) {
      setTimeout(() => {
        registerConnectionCallback();
      }, 1500);
    }
  }

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
    triggerLabCheck();
  }

  const executeSimulation = async () => {
    if (isSimulationRunning) {
      if (!api.stopSimulation())
        return
    } else {
      const activeTopologyID = simulationState.getWorldId();
      if (!activeTopologyID) {
        toast.error("Please save your topology before starting the simulation.");
        return;
      }
      if (!api.startSimulation(activeTopologyID))
        return;
    }
    setIsSimulationRunning(!isSimulationRunning);
  }

  // Handle starting a lab
  const handleStartLab = (labId: string) => {
    const lab = EXERCISES.find((l) => l.id === labId) || null;
    setActiveLab(labId)
    setLabProgress(0)
    setActiveLabObject(lab);
    if (lab) {
      toast(`You've started the "${lab.title}" lab. Follow the instructions to complete it.`);
    }
  }

  // Handle completing a lab
  const handleCompleteLab = () => {
    if (!activeLab) return

    const lab = EXERCISES.find((l) => l.id === activeLab)
    if (lab) {
      // Add to completed labs if not already there
      if (!completedLabs.includes(activeLab)) {
        setCompletedLabs((prev) => [...prev, activeLab])
      }

      // Reset active lab
      setActiveLab(null)
      setLabProgress(0)
      toast(`Congratulations! You've completed the "${lab.title}" lab.`);
    }
  }

  // Handle lab progress update
  const handleLabProgressUpdate = (completed: number, total: number) => {
    setLabProgress(completed / total * 100);

    if (completed === total) {
      handleCompleteLab();
    }
  }


  const updateNodeProperties = (properties: Partial<SimulatorNode>) => {
    if (!selectedNode) { console.warn("No node selected to update properties"); return }

    Object.keys(properties).forEach((key) => {
      if (key in selectedNode) {
        (selectedNode as any)[key] = (properties as any)[key];
      } else {
        console.warn(`Property ${key} does not exist on selected node`);
      }
    })
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 text-slate-50">
      {/* Left Sidebar */}
      <Sidebar onCreateNode={handleCreateNode} />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top Navigation Bar */}
        <TopBar
          simulationStateUpdateCount={simulationStateUpdateCount}
          onStartLab={handleStartLab}
          completedLabs={completedLabs}
          updateLabProgress={handleLabProgressUpdate}
          onOpenAIPanel={() => setIsAIPanelOpen(true)}
        />

        {/* Main Workspace */}
        <div className="flex-1 flex overflow-hidden">
          {/* Network Canvas */}
          <div className="flex-1 relative overflow-hidden">
            <NetworkCanvas
              ref={networkCanvasRef}
              onNodeSelect={onSelectedNodeChanged}
              isSimulationRunning={isSimulationRunning}
              simulationTime={currentTime}
              activeMessages={activeMessages}
            />

            {/* Active Lab Indicator */}
            {activeLabObject && (
              <ActiveLabIndicator activeLab={activeLabObject} progress={labProgress} />
            )}

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
          <div className="w-96 border-l border-slate-700 bg-slate-800 flex flex-col">


            {/* Always visible log summary widget */}
            {isSimulationRunning ?
              <RealtimeLogSummary isSimulationRunning={isSimulationRunning} onMinimizedChange={setIsLogSummaryMinimized} /> : null}

            <div
              className={`overflow-y-auto transition-all duration-300 ${isSimulationRunning && !isLogSummaryMinimized ? "flex-1" : "flex-1"
                }`}
            >
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full h-full">
                <TabsList className="w-full grid grid-cols-4">
                  {selectedNode instanceof ClassicalHost ? <TabsTrigger value="messages">Messages</TabsTrigger> : null}
                  <TabsTrigger value="logs">Logs</TabsTrigger>
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="json-view">JSON View</TabsTrigger>
                </TabsList>
                <div
                  className={`transition-all duration-300 ${isSimulationRunning && !isLogSummaryMinimized ? "h-[calc(100vh-280px)]" : isSimulationRunning ? "h-[calc(100vh-180px)]" : "h-[calc(100vh-80px)]"
                    }`}
                >

                  <TabsContent value="messages" className="p-4 h-full overflow-y-auto">
                    <MessagingPanel
                      selectedNode={selectedNode}
                      onSendMessage={handleSendMessage}
                      isSimulationRunning={isSimulationRunning}
                    />
                  </TabsContent>
                  <TabsContent value="logs" className="p-4 h-full overflow-y-auto">
                    <SimulationLogsPanel />
                  </TabsContent>
                  <TabsContent value="details" className="p-4 h-full overflow-y-auto">
                    <NodeDetailPanel
                      selectedNode={selectedNode}
                      updateNodeProperties={updateNodeProperties}
                      onSendMessage={handleSendMessage}
                      isSimulationRunning={isSimulationRunning}
                    />
                  </TabsContent>
                  <TabsContent value="json-view" className="p-4 h-full overflow-y-auto">
                    <JSONFormatViewer />
                  </TabsContent>
                </div>
              </Tabs>
            </div>
          </div>
        </div>

        {/* Timeline at Bottom */}
        {/* <div className="h-24 border-t border-slate-700 bg-slate-800">
          <SimulationTimeline currentTime={currentTime} onTimeChange={setCurrentTime} isRunning={isSimulationRunning} />
        </div> */}
      </div>
      {/* Add the AI Agents modal just before the closing div of the main component */}
      <AIAgentsModal isOpen={isAIPanelOpen} onClose={() => setIsAIPanelOpen(false)} />
    </div>
  )
}

