"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CheckCircle2, XCircle, Clock, Beaker, ArrowRight, Award } from "lucide-react"
import { EXERCISES } from "./exercise "
import { exportToJSON } from "@/services/exportService"
import { getLogger } from "@/helpers/simLogger"
import { manager } from "../node/nodeManager"
import { ConnectionManager } from "../node/connections/connectionManager"
import { getSimulationNodeTypeString } from "../node/base/enums"
import { SocketIOClient } from "@/services/socket"

interface LabPanelProps {
  isOpen: boolean
  onClose: () => void
  onStartLab: (labId: string) => void
  simulationState: any
  updateLabProgress: (completed: number, total: number) => void
}

export function LabPanel({ isOpen, onClose, onStartLab, simulationState, updateLabProgress }: LabPanelProps) {
  const logger = getLogger("LabPanel");
  const [selectedLab, setSelectedLab] = useState<string | null>(null)
  const [activeLab, setActiveLab] = useState<string | null>(null)
  const [completedLabs, setCompletedLabs] = useState<string[]>([])


  // Check if lab requirements are met
  /**
   * Checks if a lab is completed based on its requirements and the current network state.
   *
   * @param labId - The unique identifier of the lab to check for completion.
   * @returns A boolean indicating whether the lab is completed (`true`) or not (`false`).
   *
   * ### Logic:
   * 1. Retrieves the lab configuration using the provided `labId`.
   * 2. Exports the current network state and validates its existence.
   * 3. Counts the occurrences of each node type in the current network.
   * 4. Verifies if all required node types are present in the network:
   *    - Decrements the count for each matched node type to ensure accurate validation.
   * 5. Checks if all required connections exist in the network:
   *    - Validates bidirectional connections between specified node types.
   * 6. Calculates the total and fulfilled requirements to update lab progress.
   * 7. Returns `true` if all node and connection requirements are satisfied; otherwise, `false`.
   *
   * ### Why this is needed:
   * This function is essential for determining the progress and completion status of a lab.
   * It ensures that the user has met all the specified requirements (nodes and connections)
   * for a lab, enabling the application to provide feedback, track progress, and unlock
   * subsequent labs or features based on completion.
   */
  const checkLabCompletion = (labId: string) => {
    const lab = EXERCISES.find((l) => l.id === labId)
    if (!lab) return false

    const { requirements } = lab

    const currentNetwork = exportToJSON();
    if (!currentNetwork) {
      logger.error("No network found.");
      return false;
    }

    // Count the occurrences of each node type in the current network
    const nodeCounts = manager.getAllNodes().reduce((acc: Record<string, number>, node) => {
      acc[node.nodeType] = (acc[node.nodeType] || 0) + 1; // Increment count for each node type
      return acc;
    }, {});

    // Check if all required node types exist in the network
    const nodesExist = requirements.nodes.every((reqNodeType) => {
      if (nodeCounts[reqNodeType]) {
        nodeCounts[reqNodeType]--; // Decrement the count for the matched node type
        return true; // Requirement for this node type is fulfilled
      }
      return false; // Requirement for this node type is not fulfilled
    });

    const connectionsExist = requirements.connections.every(([source, target]) => {
      return ConnectionManager.getInstance().getAllConnections().some((connection) => {
        return connection.metaData.from.nodeType === source && connection.metaData.to?.nodeType === target ||
          connection.metaData.to?.nodeType === source && connection.metaData.from.nodeType === target;
      });
    })

    const socket = SocketIOClient.getInstance();
    const messagesSent = !requirements.messages || (socket.simulationEventLogs.length ?? 0) >= requirements.messages

    const totalRequirements = requirements.nodes.length + requirements.connections.length + (requirements.messages ? 1 : 0);
    const fulfilledRequirements =
      (nodesExist ? requirements.nodes.length : 0) +
      (connectionsExist ? requirements.connections.length : 0) + 
      (requirements.messages && messagesSent ? 1 : 0);

    updateLabProgress(fulfilledRequirements, totalRequirements);

    return nodesExist && connectionsExist && messagesSent;
  }

  // Check for lab completion when simulation state changes
  useEffect(() => {
    if (activeLab && checkLabCompletion(activeLab)) {
      // Mark lab as completed
      if (!completedLabs.includes(activeLab)) {
        setCompletedLabs((prev) => [...prev, activeLab])
      }
    }
  }, [simulationState, activeLab, completedLabs])

  // Get status badge for a lab
  const getLabStatusBadge = (labId: string) => {
    if (completedLabs.includes(labId)) {
      return (
        <Badge className="bg-green-900/30 text-green-400 hover:bg-green-900/40">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Completed
        </Badge>
      )
    }

    if (activeLab === labId) {
      return (
        <Badge className="bg-amber-900/30 text-amber-400 hover:bg-amber-900/40">
          <Clock className="h-3 w-3 mr-1" />
          In Progress
        </Badge>
      )
    }

    return (
      <Badge className="bg-slate-700 text-slate-300">
        <Beaker className="h-3 w-3 mr-1" />
        Not Started
      </Badge>
    )
  }

  // Get difficulty badge color
  const getDifficultyBadge = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case "beginner":
        return "bg-blue-900/30 text-blue-400 hover:bg-blue-900/40"
      case "intermediate":
        return "bg-amber-900/30 text-amber-400 hover:bg-amber-900/40"
      case "advanced":
        return "bg-red-900/30 text-red-400 hover:bg-red-900/40"
      default:
        return "bg-slate-700 text-slate-300"
    }
  }

  const onLabCancel = () => {
    setActiveLab(null);
    setSelectedLab(null);
  }

  // Calculate overall progress
  const overallProgress = (completedLabs.length / EXERCISES.length) * 100

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
      <div className="bg-slate-900 border border-slate-700 rounded-lg w-[800px] max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <Beaker className="h-5 w-5 text-blue-400" />
            <h2 className="text-xl font-semibold">Quantum Network Labs</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <XCircle className="h-5 w-5" />
          </Button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Lab List */}
          <div className="w-1/3 border-r border-slate-700 p-4">
            <div className="mb-4">
              <h3 className="text-sm font-medium text-slate-400 mb-2">Your Progress</h3>
              <Progress value={overallProgress} className="h-2" />
              <div className="flex justify-between mt-1 text-xs text-slate-500">
                <span>
                  {completedLabs.length} of {EXERCISES.length} completed
                </span>
                <span>{Math.round(overallProgress)}%</span>
              </div>
            </div>

            <ScrollArea className="h-[calc(80vh-150px)]">
              <div className="space-y-2">
                {EXERCISES.map((lab) => (
                  <Card
                    key={lab.id}
                    className={`cursor-pointer transition-colors ${selectedLab === lab.id ? "border-blue-500" : "border-slate-700"
                      }`}
                    onClick={() => setSelectedLab(lab.id)}
                  >
                    <CardHeader className="p-3">
                      <div className="flex justify-between items-start">
                        <CardTitle className="text-sm">{lab.title}</CardTitle>
                        {getLabStatusBadge(lab.id)}
                      </div>
                      <CardDescription className="text-xs">{lab.description}</CardDescription>
                    </CardHeader>
                    <CardFooter className="p-3 pt-0 flex justify-between items-center">
                      <Badge className={getDifficultyBadge(lab.difficulty)}>{lab.difficulty}</Badge>
                      <span className="text-xs text-slate-400">{lab.estimatedTime}</span>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* Lab Details */}
          <div className="flex-1 p-4 flex flex-col overflow-auto">
            {selectedLab ? (
              <>
                {(() => {
                  const lab = EXERCISES.find((l) => l.id === selectedLab)
                  if (!lab) return null

                  return (
                    <>
                      <div className="mb-4">
                        <h2 className="text-xl font-semibold mb-1">{lab.title}</h2>
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className={getDifficultyBadge(lab.difficulty)}>{lab.difficulty}</Badge>
                          <span className="text-sm text-slate-400">{lab.estimatedTime}</span>
                          {getLabStatusBadge(lab.id)}
                        </div>
                        <p className="text-slate-300">{lab.description}</p>
                      </div>

                      <Tabs defaultValue="instructions" className="flex-1 flex flex-col">
                        <TabsList>
                          <TabsTrigger value="instructions">Instructions</TabsTrigger>
                          <TabsTrigger value="tips">Tips & Hints</TabsTrigger>
                          <TabsTrigger value="requirements">Requirements</TabsTrigger>
                        </TabsList>

                        <TabsContent value="instructions" className="flex-1 overflow-auto">
                          <div className="space-y-4">
                            <h3 className="text-lg font-medium">Step-by-Step Instructions</h3>
                            <ol className="space-y-2 list-decimal list-inside">
                              {lab.steps.map((step, index) => (
                                <li key={index} className="text-slate-300">
                                  {step}
                                </li>
                              ))}
                            </ol>
                          </div>
                        </TabsContent>

                        <TabsContent value="tips" className="flex-1 overflow-auto">
                          <div className="space-y-4">
                            <h3 className="text-lg font-medium">Tips & Hints</h3>
                            <ul className="space-y-2 list-disc list-inside">
                              {lab.tips.map((tip, index) => (
                                <li key={index} className="text-slate-300">
                                  {tip}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </TabsContent>

                        <TabsContent value="requirements" className="flex-1 overflow-auto">
                          <div className="space-y-4">
                            <h3 className="text-lg font-medium">Completion Requirements</h3>
                            <div className="space-y-2">
                              {lab.requirements.nodes && (
                                <div>
                                  <h4 className="text-sm font-medium">Required Nodes:</h4>
                                  <ul className="list-disc list-inside">
                                    {Object.entries(
                                      lab.requirements.nodes.reduce((acc: Record<string, number>, node) => {
                                        acc[node] = (acc[node] || 0) + 1
                                        return acc
                                      }, {})
                                    ).map(([node, count], index) => (
                                      <li key={index} className="text-slate-300">
                                        {getSimulationNodeTypeString(+node)} x {count}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {lab.requirements.connections && (
                                <div>
                                  <h4 className="text-sm font-medium">Required Connections:</h4>
                                  <ul className="list-disc list-inside">
                                    {lab.requirements.connections.map(([source, target], index) => (
                                      <li key={index} className="text-slate-300">
                                        {getSimulationNodeTypeString(source)} to {getSimulationNodeTypeString(target)}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {lab.requirements.entanglement && (
                                <div>
                                  <h4 className="text-sm font-medium">Entanglement:</h4>
                                  <p className="text-slate-300">Create at least one entangled qubit pair</p>
                                </div>
                              )}

                              {lab.requirements.messages && (
                                <div>
                                  <h4 className="text-sm font-medium">Messages:</h4>
                                  <p className="text-slate-300">Send at least {lab.requirements.messages} messages</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </TabsContent>
                      </Tabs>

                      <div className="mt-4 flex justify-end">
                        {completedLabs.includes(lab.id) ? (
                          <Button className="gap-2" disabled>
                            <Award className="h-4 w-4" />
                            Completed
                          </Button>
                        ) : activeLab === lab.id ? (
                          <Button variant="destructive" onClick={() => onLabCancel()}>
                            Cancel Lab
                          </Button>
                        ) : (
                          <Button
                            className="gap-2 bg-green-500"
                            onClick={() => {
                              setActiveLab(lab.id)
                              onStartLab(lab.id)
                              onClose()
                            }}
                          >
                            Start Lab
                            <ArrowRight className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </>
                  )
                })()}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Beaker className="h-16 w-16 text-slate-600 mb-4" />
                <h3 className="text-xl font-medium mb-2">Select a Lab</h3>
                <p className="text-slate-400 max-w-md">
                  Choose a lab from the list to view instructions and requirements. Complete labs to track your progress
                  in quantum networking.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
