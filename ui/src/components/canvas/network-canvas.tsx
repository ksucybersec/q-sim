"use client"

import { useRef, useEffect, useState, useCallback, forwardRef, useImperativeHandle, useLayoutEffect } from "react"
import { motion } from "framer-motion"
import { FabricJSCanvas, useFabricJSEditor } from 'fabricjs-react';
import { getLogger } from "@/helpers/simLogger"
import { SimulatorNode, SimulatorNodeOptions } from "../node/base/baseNode";
import { ConnectionManager } from "../node/connections/connectionManager";
import { KeyboardListener } from "./keyboard";
import { NetworkManager } from "../node/network/networkManager";
import { SimulationNodeType, getSimulationNodeTypeString } from "../node/base/enums";
import { manager } from "../node/nodeManager";
import * as fabric from "fabric";
import "./canvas.scss";
import api from "@/services/api";
import { getNewNode } from "./utils";
import { WebSocketClient } from "@/services/socket";
import { importFromJSON } from "@/services/importService";
import { NetworkAnimationController } from "./animation";
import { networkStorage } from "@/services/storage";
import { toast } from "sonner";
import simulationState from "@/helpers/utils/simulationState";
import { getCompatibleNextNodeTypes } from "@/helpers/topologyHelper";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Plus } from "lucide-react";

import { debounce } from "lodash"; // Import debounce from lodash

interface NetworkCanvasProps {
  onNodeSelect: (node: any) => void
  isSimulationRunning: boolean
  simulationTime: number
  activeMessages?: any[]
  quickAddHelperEnabled?: boolean
  onQuickAddNodeAdded?: () => void
}

export const NetworkCanvas = forwardRef(({ onNodeSelect, isSimulationRunning, simulationTime, activeMessages = [], quickAddHelperEnabled = true, onQuickAddNodeAdded }: NetworkCanvasProps, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const quickAddOverlayRef = useRef<HTMLDivElement>(null);
  const { editor, onReady } = useFabricJSEditor();
  const [nodes, setNodes] = useState([]);
  const [hoveredNode, setHoveredNode] = useState<SimulatorNode | null>(null);
  const [quickAddMenuOpen, setQuickAddMenuOpen] = useState(false);
  const [quickAddPosition, setQuickAddPosition] = useState<{ left: number; top: number } | null>(null);

  const logger = getLogger("Canvas");

  const updateQuickAddPosition = useCallback(() => {
    const canvas = editor?.canvas as fabric.Canvas;
    const node = hoveredNode;
    if (!canvas || !node || !containerRef.current) {
      setQuickAddPosition(null);
      return;
    }
    const vpt = (canvas as any).viewportTransform as number[] | undefined;
    if (!vpt || vpt.length < 6) {
      setQuickAddPosition(null);
      return;
    }
    // Overlap button with node so pointer stays over node until it hits the button (no gap = no disappear)
    const overlapPx = 14;
    const sx = node.getX() + node.width - overlapPx;
    const sy = node.getY() + node.height / 2;
    const vx = vpt[0] * sx + vpt[2] * sy + vpt[4];
    const vy = vpt[1] * sx + vpt[3] * sy + vpt[5];
    const wrapper = containerRef.current.querySelector(".canvas-container") as HTMLElement | null;
    if (!wrapper) {
      setQuickAddPosition({ left: vx, top: vy });
      return;
    }
    const wrapperRect = wrapper.getBoundingClientRect();
    const containerRect = containerRef.current.getBoundingClientRect();
    const cw = (canvas as any).width ?? wrapperRect.width;
    const ch = (canvas as any).height ?? wrapperRect.height;
    const scaleX = wrapperRect.width / cw;
    const scaleY = wrapperRect.height / ch;
    setQuickAddPosition({
      left: wrapperRect.left - containerRect.left + vx * scaleX,
      top: wrapperRect.top - containerRect.top + vy * scaleY,
    });
  }, [editor, hoveredNode]);

  useEffect(() => {
    if (!hoveredNode || !quickAddHelperEnabled) {
      setQuickAddPosition(null);
      return;
    }
    updateQuickAddPosition();
    const canvas = editor?.canvas as fabric.Canvas;
    if (!canvas) return;
    const onRender = () => updateQuickAddPosition();
    canvas.on("after:render", onRender);
    return () => {
      canvas.off("after:render", onRender);
    };
  }, [hoveredNode, quickAddHelperEnabled, updateQuickAddPosition, editor]);

  useEffect(() => {
    if (!quickAddMenuOpen) return;
    const onMouseDown = (e: MouseEvent) => {
      if (quickAddOverlayRef.current?.contains(e.target as Node)) return;
      setQuickAddMenuOpen(false);
    };
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, [quickAddMenuOpen]);

  useLayoutEffect(() => {
    setTimeout(async () => {
      const socketHost = process.env.NODE_ENV === 'production' ? window.location.toString() : 'http://localhost:5174';
      const socketUrl = new URL(socketHost.replace("http", "ws"));
      socketUrl.pathname = "/api/ws";
      WebSocketClient.getInstance().connect(socketUrl.toString());

      NetworkAnimationController.getInstance(editor?.canvas as fabric.Canvas);
    }, 2500);
  }, [editor]);

  // useEffect(() => {
  //   debouncedCheckImport();
  // }, [editor])

  // For some unknown reason, two canvases are generated. So, we debounce the import check to avoid rending on unseen canvas.
  const debouncedCheckImport = debounce(async (canvas?: fabric.Canvas) => {
    const queryParams = new URLSearchParams(window.location.search);
    const lastOpenedTopologyID = queryParams.get("topologyID") || (await networkStorage.getLastOpenedTopologyID());

    let topologyID = null;
    console.log(lastOpenedTopologyID, simulationState.getWorldId());
    if (lastOpenedTopologyID) {
      if (lastOpenedTopologyID === simulationState.getWorldId()) {
        return;
      }
      topologyID = lastOpenedTopologyID;
    }

    if (topologyID) {
      try {
        const savedTopology = await api.getTopology(topologyID);
        if (savedTopology?.zones) {
          canvas = (editor?.canvas as fabric.Canvas) || canvas;
          if (!canvas) {
            logger.warn("Canvas not found in editor", editor);
            return;
          }
          importFromJSON(savedTopology, canvas);
          onFirstNodeAdded(canvas);
        }
      } catch (e) {
        toast("Topology not found!", {
          onAutoClose: (t) => {
            window.location.href = "/";
          },
        });
      }
    }
  }, 1300);

  // Update canvas when simulation state changes
  useEffect(() => {
    // Animate quantum states if simulation is running
    if (isSimulationRunning) {
      // Animation logic would go here
    }
  }, [isSimulationRunning, simulationTime, activeMessages])


  const drawMessagePacket = (ctx: CanvasRenderingContext2D, x: number, y: number, protocol: string) => {
    // Draw different packet styles based on protocol
    console.log("Draw Packet")
  }

  const animatePacket = async () => {
    // Draw active messages
    activeMessages.forEach((message) => {
      const sourceNode = nodes[message.source]
      const targetNode = nodes[message.target]

      if (sourceNode && targetNode) {
        // Calculate message position based on progress
        const progress = (simulationTime - message.startTime) / message.duration
      }
    })
  }

  const fabricRendered = async (canvas: fabric.Canvas) => {
    // Prevent multiple initializations
    // if (fabricInitialized.current) return;
    // fabricInitialized.current = true;

    if (editor?.canvas) {
      console.log("Canvas already initialized, skipping");
      return;
    }


    onReady(canvas);

    debouncedCheckImport(canvas);

    canvas.on('mouse:down', (e) => {
      const selectedNode = e.target;
      onNodeSelect(selectedNode);
    });

    canvas.on("mouse:move", (e: any) => {
      const target = e.target;
      if (target && target instanceof SimulatorNode) {
        setHoveredNode(target);
      } else {
        setHoveredNode(null);
      }
    });
    // Don’t clear on canvas mouse:out — button overlaps node so we clear only when pointer leaves the overlay
  }


  const onSimulatorEvent = (event: any) => {
    console.log(event)
  }

  const onFirstNodeAdded = (canvas?: fabric.Canvas) => {
    ConnectionManager.getInstance(editor?.canvas || canvas);
    KeyboardListener.getInstance(editor?.canvas || canvas);
    NetworkManager.getInstance(editor?.canvas || canvas);
    // api.startAutoUpdateNetworkTopology();
  };

  const addNodeToCanvas = (fabricObject: fabric.FabricObject) => {
    editor?.canvas.add(fabricObject);

    if (editor?.canvas.getObjects().length === 1) {
      onFirstNodeAdded();
    }
  };

  const createNewNode = async (type: SimulationNodeType, x: number, y: number) => {
    const nodeManager = manager;

    if (!nodeManager) {
      logger.error("NodeManager is not initialized.");
      return;
    }

    const newNode = getNewNode(type, x, y, editor?.canvas as fabric.Canvas)

    if (newNode) {
      addNodeToCanvas(newNode); // Add Fabric.js object to canvas
      setNodes((prevNodes): any => [...prevNodes, newNode.getNodeInfo()]);
    }
  }

  const createNodeCallback = useCallback(createNewNode, [editor]); // Dependency array includes editor and createNode

  const addConnectedNode = useCallback((fromNode: SimulatorNode, newNodeType: SimulationNodeType) => {
    const canvas = editor?.canvas as fabric.Canvas;
    if (!canvas) return;
    const offsetX = 80;
    const x = fromNode.getX() + fromNode.width + offsetX;
    const y = fromNode.getY();
    const newNode = getNewNode(newNodeType, x, y, canvas);
    if (newNode) {
      addNodeToCanvas(newNode);
      setNodes((prevNodes): any => [...prevNodes, newNode.getNodeInfo()]);
      ConnectionManager.getInstance(canvas).createConnectionBetween(fromNode, newNode);
    }
  }, [editor]);

  useImperativeHandle(ref, () => ({
    addConnectedNode,
    handleCreateClassicalHost: () => {
      createNodeCallback(SimulationNodeType.CLASSICAL_HOST, 50, 50);
    },
    handleCreateClassicalRouter: () => {
      createNodeCallback(SimulationNodeType.CLASSICAL_ROUTER, 150, 50);
    },
    handleCreateQuantumHost: () => {
      createNodeCallback(SimulationNodeType.QUANTUM_HOST, 250, 50);
    },
    handleCreateQuantumRepeater: () => {
      createNodeCallback(SimulationNodeType.QUANTUM_REPEATER, 350, 50);
    },
    handleCreateQuantumAdapter: () => {
      createNodeCallback(SimulationNodeType.QUANTUM_ADAPTER, 450, 50);
    },
    handleCreateInternetExchange: () => {
      createNodeCallback(SimulationNodeType.INTERNET_EXCHANGE, 550, 50);
    },
    handleCreateC2QConverter: () => {
      createNodeCallback(SimulationNodeType.CLASSIC_TO_QUANTUM_CONVERTER, 650, 50);
    },
    handleCreateQ2CConverter: () => {
      createNodeCallback(SimulationNodeType.QUANTUM_TO_CLASSIC_CONVERTER, 750, 50);
    },
    handleCreateZone: () => {
      createNodeCallback(SimulationNodeType.ZONE, 50, 200);
    },
    handleCreateNetwork: () => {
      createNodeCallback(SimulationNodeType.CLASSICAL_NETWORK, 50, 300);
    }
  }));

  const canvas = editor?.canvas as fabric.Canvas | undefined;
  const connectionManager = canvas ? ConnectionManager.getInstance(canvas) : null;
  const compatibleTypes = hoveredNode && connectionManager ? getCompatibleNextNodeTypes(hoveredNode, connectionManager) : [];
  const showQuickAddButton = quickAddHelperEnabled && hoveredNode && quickAddPosition != null && compatibleTypes.length > 0;

  return (
    <div ref={containerRef} className="w-full h-full bg-slate-900 relative">
      {/* <canvas
        ref={canvasRef}
        className="w-full h-full"
        onClick={(e) => {
          // Handle node selection logic here
          // For now, just a placeholder
          const rect = e.currentTarget.getBoundingClientRect()
          const x = e.clientX - rect.left
          const y = e.clientY - rect.top

          // Check if a node was clicked
          // This would be replaced with your actual node detection logic
          console.log(`Canvas clicked at (${x}, ${y})`)
        }}
      /> */}

      <FabricJSCanvas className="canvas-container w-full h-full" onReady={fabricRendered} />

      {/* Quick-add connected node: floating button next to hovered node */}
      {showQuickAddButton && quickAddPosition && (
        <motion.div
          ref={quickAddOverlayRef}
          className="absolute z-10 pointer-events-none"
          style={{ left: quickAddPosition.left, top: quickAddPosition.top, transform: "translateY(-50%)" }}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.12 }}
        >
          <div
            className="pointer-events-auto"
            onPointerLeave={() => {
              // Keep overlay (and hoveredNode) while dropdown is open so moving to menu doesn't hide it
              if (!quickAddMenuOpen) setHoveredNode(null);
            }}
          >
            <DropdownMenu open={quickAddMenuOpen} onOpenChange={setQuickAddMenuOpen}>
              <DropdownMenuTrigger asChild>
                <Button
                  size="icon"
                  variant="secondary"
                  className="h-8 w-8 rounded-full shadow-lg border border-slate-500 bg-slate-700 hover:bg-slate-600 text-slate-100 [&_svg]:text-slate-100"
                  title="Add connected node"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="min-w-[160px]">
                {compatibleTypes.map((nodeType) => (
                  <DropdownMenuItem
                    key={nodeType}
                    onClick={() => {
                      if (hoveredNode) {
                        addConnectedNode(hoveredNode, nodeType);
                        onQuickAddNodeAdded?.();
                        setQuickAddMenuOpen(false);
                      }
                    }}
                  >
                    {getSimulationNodeTypeString(nodeType)}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </motion.div>
      )}

      {/* Overlay elements for interactive components */}
      <div className="absolute top-4 right-4 bg-slate-800/80 backdrop-blur-sm p-2 rounded-md">
        <div className="text-xs text-slate-400">Simulation Time</div>
        <div className="text-lg font-mono">{simulationTime.toFixed(2)}s</div>
      </div>

      {/* Visual indicator for simulation running state */}
      {isSimulationRunning && (
        <motion.div
          className="absolute top-4 left-4 bg-green-500 h-3 w-3 rounded-full"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY }}
        />
      )}

      {/* Message count indicator */}
      {activeMessages.length > 0 && (
        <div className="absolute bottom-20 right-4 bg-slate-800/80 backdrop-blur-sm p-2 rounded-md">
          <div className="text-xs text-slate-400">Active Messages</div>
          <div className="text-lg font-mono">{activeMessages.length}</div>
        </div>
      )}
    </div>
  )
});
