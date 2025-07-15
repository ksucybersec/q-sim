"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Laptop,
  Router,
  Cpu,
  Network,
  Save,
  FolderOpen,
  Settings,
  HelpCircle,
  PlayCircle,
  Database,
  FileText,
  Workflow,
} from "lucide-react"
import { sendClickComponentEvent } from "@/helpers/userEvents/userEvents"

interface SidebarProps {
  onCreateNode: (action: string) => void;
}

export function Sidebar({ onCreateNode }: SidebarProps) {
  const [activeCategory, setActiveCategory] = useState("nodes")

  const categories = [
    { id: "nodes", icon: <Workflow className="h-5 w-5" /> },
    { id: "templates", icon: <FileText className="h-5 w-5" /> },
    { id: "simulations", icon: <PlayCircle className="h-5 w-5" /> },
    { id: "data", icon: <Database className="h-5 w-5" /> },
  ]

  const nodeTypes = [
    {
      id: "classical-host",
      name: "Classical Host",
      icon: <Laptop className="h-5 w-5" />,
      color: "bg-blue-500",
      action: "createClassicalHost",
      tooltip: "Traditional computing device that processes information using classical bits"
    },
    {
      id: "classical-router",
      name: "Classical Router",
      icon: <Router className="h-5 w-5" />,
      color: "bg-blue-600",
      action: "createClassicalRouter",
      tooltip: "Network device that directs classical data packets between different network segments"
    },
    {
      id: "quantum-host",
      name: "Quantum Host",
      icon: <Cpu className="h-5 w-5" />,
      color: "bg-green-500",
      action: "createQuantumHost",
      tooltip: "Computing device that processes quantum information using qubits and quantum operations"
    },
    {
      id: "quantum-adapter",
      name: "Quantum Adapter",
      icon: <Network className="h-5 w-5" />,
      color: "bg-green-600",
      action: "createQuantumAdapter",
      tooltip: "Interface device that converts between classical and quantum communication protocols"
    },
    {
      id: "quantum-repeater",
      name: "Quantum Repeater",
      icon: <Network className="h-5 w-5" />,
      color: "bg-purple-500",
      action: "createQuantumRepeater",
      tooltip: "Device that extends quantum communication range by amplifying and retransmitting quantum signals"
    },
    // {
    //   id: "quantum-channel",
    //   name: "Quantum Channel",
    //   icon: <Zap className="h-5 w-5" />,
    //   color: "bg-purple-600",
    //   action: "createQuantumChannel"
    // },
    // {
    //   id: "entanglement",
    //   name: "Entanglement",
    //   icon: <Share2 className="h-5 w-5" />,
    //   color: "bg-amber-500",
    //   action: "createEntanglement"
    // },
  ]


  const handleNodeClick = (node: typeof nodeTypes[0]) => {
    if (onCreateNode) {
      onCreateNode(node.action);
      sendClickComponentEvent(node.action)
    }
  }

  return (
    <div className="w-64 border-r border-slate-700 bg-slate-800 flex flex-col">
      {/* Top Icons */}
      <div className="flex justify-around p-2 border-b border-slate-700">
        {/* <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon">
                <Save className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Save Project</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon">
                <FolderOpen className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Open Project</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Settings</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon">
                <HelpCircle className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Help</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider> */}
      </div>

      {/* Category Tabs */}
      <div className="flex justify-around p-2 border-b border-slate-700 hidden">
        {categories.map((category) => (
          <TooltipProvider key={category.id}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={activeCategory === category.id ? "secondary" : "ghost"}
                  size="icon"
                  onClick={() => setActiveCategory(category.id)}
                >
                  {category.icon}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="capitalize">{category.id}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ))}
      </div>

      {/* Content Area */}
      <ScrollArea className="flex-1">
        {activeCategory === "nodes" && (
          <div className="p-4 space-y-4">
            <h3 className="text-sm font-medium text-slate-400">Network Components</h3>
            <div className="space-y-2">
              {nodeTypes.map((node) => (

                // <div
                //   key={node.id}
                //   className="flex items-center gap-3 p-2 rounded-md hover:bg-slate-700 cursor-move"
                //   draggable
                //   onClick={() => handleNodeClick(node)}
                // >
                //   <div className={`p-1.5 rounded-md ${node.color}`}>{node.icon}</div>
                //   <span className="text-sm">{node.name}</span>
                // </div>
                <span key={node.id}>

                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div
                          key={node.id}
                          className="flex items-center gap-3 p-2 rounded-md hover:bg-slate-700 cursor-move"
                          draggable
                          onClick={() => handleNodeClick(node)}
                        >
                          <div className={`p-1.5 rounded-md ${node.color}`}>{node.icon}</div>
                          <span className="text-sm">{node.name}</span>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        {node.tooltip && <p> {node.tooltip}</p>}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </span>
              ))}
            </div>

            <Separator />

            {/* <h3 className="text-sm font-medium text-slate-400">Saved Components</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-3 p-2 rounded-md hover:bg-slate-700 cursor-move">
                <div className="p-1.5 rounded-md bg-amber-500">
                  <Cpu className="h-5 w-5" />
                </div>
                <span className="text-sm">BB84 Node</span>
              </div>
              <div className="flex items-center gap-3 p-2 rounded-md hover:bg-slate-700 cursor-move">
                <div className="p-1.5 rounded-md bg-amber-500">
                  <Network className="h-5 w-5" />
                </div>
                <span className="text-sm">Quantum Repeater</span>
              </div>
            </div> */}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}

