"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Beaker, ChevronDown, ChevronUp, CheckCircle2 } from "lucide-react"
import { getSimulationNodeTypeString } from "../node/base/enums"
import { ExerciseI } from "./exercise/exercise"

interface ActiveLabIndicatorProps {
  activeLab: ExerciseI | null
  progress: number
  onComplete?: () => void
}

export function ActiveLabIndicator({ activeLab, progress, onComplete }: ActiveLabIndicatorProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!activeLab) return null

  return (
    <Card className="absolute top-16 right-4 w-80 bg-slate-200/90 backdrop-blur-sm border-slate-700 shadow-lg">
      <CardHeader className="p-3 pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Beaker className="h-4 w-4 text-blue-400" />
            <CardTitle className="text-sm font-medium">Active Lab</CardTitle>
          </div>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => setIsExpanded(!isExpanded)}>
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-0">
        <h3 className="font-medium text-sm">{activeLab.title}</h3>
        <div className="mt-2">
          <Progress value={progress} className="h-1.5" />
          <div className="flex justify-between mt-1">
            <span className="text-xs text-slate-400">Progress</span>
            <span className="text-xs font-medium">{Math.round(progress)}%</span>
          </div>
        </div>

        {isExpanded && (
          <div className="mt-3 space-y-2">
            <div className="text-xs text-slate-500">{activeLab.description}</div>
            <div>
              <h3 className=" mb-1 font-bold">Requirements:</h3>
              <div className="text-xs bg-slate-100 p-2 rounded">

                {activeLab.requirements.nodes && (
                  <div>
                    <h4 className="text-sm font-medium">Required Nodes:</h4>
                    <ul className="list-disc list-inside">
                      {Object.entries(
                        activeLab.requirements.nodes.reduce((acc: Record<string, number>, node) => {
                          acc[node] = (acc[node] || 0) + 1
                          return acc
                        }, {})
                      ).map(([node, count], index) => (
                        <li key={index} className="text-slate-800">
                          {getSimulationNodeTypeString(+node)} X {count}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {activeLab.requirements.connections && (
                  <div>
                    <h4 className="text-sm font-medium">Required Connections:</h4>
                    <ul className="list-disc list-inside">
                      {activeLab.requirements.connections.map(([source, target], index) => (
                        <li key={index} className="text-slate-800">
                          {getSimulationNodeTypeString(source)} to {getSimulationNodeTypeString(target)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {activeLab.requirements.messages && (
                  <div>
                    <h4 className="text-sm font-medium">Messages:</h4>
                    <p className="text-slate-800">Send at least {activeLab.requirements.messages} messages</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
      {progress >= 100 && (
        <CardFooter className="p-3 pt-0">
          <Button className="w-full text-xs h-8 gap-1" onClick={onComplete}>
            <CheckCircle2 className="h-3 w-3" />
            Mark as Complete
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
