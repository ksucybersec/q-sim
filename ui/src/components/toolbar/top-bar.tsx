import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ChevronDown, RotateCcw, Beaker, Check, Bot, Pause, Play, User, LogOut } from "lucide-react"
import { downloadJson, exportToJSON } from "@/services/exportService"
import api from "@/services/api"
import { useEffect, useState } from "react"
import { LabPanel } from "../labs/lab-panel"
import { Badge } from "../ui/badge"
import { EXERCISES } from "../labs/exercise "
import { ExportDataI } from "@/services/export.interface"
import simulationState from "@/helpers/utils/simulationState"
import { ClickEventButton } from "@/helpers/components/butonEvent/clickEvent"
import { UserEventType } from "@/helpers/userEvents/userEvents.enums"

interface TopBarProps {
  onStartLab?: (labId: string | null) => void
  completedLabs?: string[]
  simulationStateUpdateCount: any
  updateLabProgress: (completed: number, total: number) => void
  onOpenAIPanel?: () => void,
  isRunning: boolean
  toggleSimulation: () => void
}

export function TopBar({
  onStartLab = () => { },
  completedLabs = [],
  simulationStateUpdateCount,
  updateLabProgress,
  onOpenAIPanel = () => { },
  isRunning,
  toggleSimulation,
}: TopBarProps
) {
  const [isAIEnabled, setIsAIEnabled] = useState(false)
  const [isLabPanelOpen, setIsLabPanelOpen] = useState(false)
  const [savedTopologies, setSavedTopologies] = useState([])

  useEffect(() => {
    api.getConfig().then((config) => {
      setIsAIEnabled(config.enable_ai_feature);
    })
  }, [])

  const fetchSavedTopologies = async () => {
    const response = await api.listSavedTopologies();
    if (response) {
      setSavedTopologies(response);
    }
  }

  const exportJSONFile = () => {
    const jsonData = exportToJSON();

    if (!jsonData) return;

    downloadJson(jsonData, "network")
  }

  const saveCurrentNetwork = async () => {
    const jsonData = exportToJSON();

    if (!jsonData) return;

    const activeTopologyID = simulationState.getWorldId();
    if (activeTopologyID)
      jsonData.pk = activeTopologyID;
    else
      jsonData.name = prompt("Enter a name for the topology") || "Untitled Topology";

    const response = await api.saveTopology(jsonData);

    if (response?.pk) {
      simulationState.setWorldId(response.pk);
    } else {
      console.error("Failed to save topology");
    }
  }

  return (
    <>

      <div className="h-12 border-b border-slate-700 bg-slate-800 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
            Quantum Network Simulator
          </h1>

          <div className="flex items-center">
            <DropdownMenu onOpenChange={fetchSavedTopologies}>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 gap-1">
                  File <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => (window.location.href = "/")}>New Project</DropdownMenuItem>
                <DropdownMenuItem onClick={saveCurrentNetwork}>Save</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={exportJSONFile}>Export...</DropdownMenuItem>
                <DropdownMenuItem>Import...</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>Load Saved Topology</DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      {
                        savedTopologies.length === 0 ?
                          <DropdownMenuItem disabled>
                            No saved topologies found.
                          </DropdownMenuItem>
                          :
                          savedTopologies.map((topology: ExportDataI) => (
                            <DropdownMenuItem
                              key={topology.pk}
                              onClick={() => {
                                window.location.href = `/?topologyID=${topology.pk}`;
                              }}
                            >
                              {topology.name}
                            </DropdownMenuItem>
                          ))
                      }
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* New Lab Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 gap-1">
                  Lab <ChevronDown className="h-4 w-4" />
                  <Badge className="ml-1 h-5 bg-blue-600 hover:bg-blue-700">
                    {completedLabs.length}/{EXERCISES.length}
                  </Badge>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setIsLabPanelOpen(true)}>
                  <Beaker className="h-4 w-4 mr-2" />
                  Browse Labs
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {
                  EXERCISES.map((exercise) => (
                    <DropdownMenuItem key={exercise.id}>
                      {exercise.title}
                      {completedLabs.includes(exercise.id) && <Check className="h-4 w-4 ml-2 text-green-500" />}
                    </DropdownMenuItem>
                  ))
                }
              </DropdownMenuContent>
            </DropdownMenu>

          </div>
        </div>

        <div className="flex items-center gap-2">
          <ClickEventButton elementType="Simulation Button" elementDescription={isRunning ? "Stop Simulation" : "Start Simulation"} 
          eventType={isRunning ? UserEventType.SIMULATION_COMPLETE : UserEventType.SIMULATION_START}>
            <Button size="sm" className="h-8 gap-1" onClick={toggleSimulation} variant={isRunning ? "destructive" : "secondary"}>
              {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {isRunning ? "Stop" : "Run"} Simulation
            </Button>
          </ClickEventButton>

          {
            isAIEnabled &&
            <ClickEventButton elementType="AI Agent Button" elementDescription="Click to open AI Agent Panel From Top bar" eventType={UserEventType.AI_AGENT_OPEN}>
              <Button size="sm" className="h-8 gap-1" onClick={onOpenAIPanel}>
                <Bot className="h-4 w-4" />
                AI Agents
              </Button>
            </ClickEventButton>
          }

          <Button onClick={() => { simulationState.clearUserName(); location.replace('/'); }}>
            <User className="h-4 w-4"></User>
            {simulationState.getUserName()}
            <LogOut className="ml-2"></LogOut>
          </Button>

          <Button variant="ghost" size="icon" className="h-8 w-8">
            <RotateCcw className="h-4 w-4" />
          </Button>

        </div>
      </div>

      {/* Lab Panel */}
      <LabPanel
        isOpen={isLabPanelOpen}
        onClose={() => setIsLabPanelOpen(false)}
        simulationState={simulationStateUpdateCount}
        onStartLab={onStartLab}
        updateLabProgress={updateLabProgress}
      />
    </>
  )
}

