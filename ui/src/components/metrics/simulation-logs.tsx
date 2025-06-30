"use client"

import { ScrollArea } from "@radix-ui/react-scroll-area"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, Info, CheckCircle, Search } from "lucide-react"
import { WebSocketClient } from "@/services/socket"
import { convertEventToLog } from "./log-parser"
import { Input } from "../ui/input"

export interface LogI {
  level: string
  time: string
  source: string
  message: string
}

export function SimulationLogsPanel() {
  const socket = WebSocketClient.getInstance()

  const [logFilter, setLogFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [simulationLogs, setSimulationLogs] = useState<LogI[]>(
    socket.simulationEventLogs
      .reverse()
      .map((x) => convertEventToLog(x))
      .filter((x) => x !== undefined),
  )

  useEffect(() => {
    const handleEvent = (event: any) => {
      const converted = convertEventToLog(event)
      if (converted) setSimulationLogs((prevLogs) => [converted, ...prevLogs])
    }

    socket.onMessage("simulation_event", handleEvent)

    // Clean up the event listener on unmount
    return () => {
      socket.offMessage("simulation_event", handleEvent)
    }
  }, []) // Empty dependency array so this only runs once

  // Filter logs based on level and search query
  const filteredLogs = simulationLogs.filter((log) => {
    const matchesLevel = logFilter === "all" || log.level === logFilter
    const matchesSearch =
      searchQuery === "" ||
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.source.toLowerCase().includes(searchQuery.toLowerCase())

    return matchesLevel && matchesSearch
  })

  // Function to get the appropriate icon for log level
  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case "error":
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-amber-500" />
      case "info":
        return <Info className="h-4 w-4 text-blue-500" />
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      default:
        return <Info className="h-4 w-4 text-blue-500" />
    }
  }

  // Function to get the appropriate badge color for log level
  const getLogLevelBadge = (level: string) => {
    switch (level) {
      case "error":
        return "bg-red-900/30 text-red-400 hover:bg-red-900/40"
      case "warning":
        return "bg-amber-900/30 text-amber-400 hover:bg-amber-900/40"
      case "info":
        return "bg-blue-900/30 text-blue-400 hover:bg-blue-900/40"
      case "success":
        return "bg-green-900/30 text-green-400 hover:bg-green-900/40"
      default:
        return "bg-slate-800 hover:bg-slate-700"
    }
  }

  const clearLogs = () => {
    setSimulationLogs([])
    socket.simulationEventLogs = []
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Simulator Logs</h3>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            placeholder="Search logs..."
            className="pl-8"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="bg-slate-900 rounded-md border border-slate-700 flex flex-col flex-1 min-h-0">
        <div className="grid grid-cols-12 gap-2 p-2 border-b border-slate-700 text-xs font-medium text-slate-400">
          <div className="col-span-1">Level</div>
          <div className="col-span-2">Time</div>
          <div className="col-span-3">Source</div>
          {/* <div className="col-span-6">Message</div> */}
        </div>

        <ScrollArea className="flex-1 overflow-x-auto">
          <div className="space-y-1 p-2">
            {filteredLogs.length > 0 ? (
              filteredLogs.map((log, idx) => (
                <div key={idx} className="grid grid-cols-6 gap-2 p-2 text-sm rounded hover:bg-slate-800">
                  <div className="col-span-1 flex items-center">
                    <Badge className={`flex h-6 items-center gap-1 px-2 ${getLogLevelBadge(log.level)}`}>
                      {getLogLevelIcon(log.level)}
                    </Badge>
                  </div>
                  <div className="col-span-2 font-mono text-slate-400">{log.time}</div>
                  <div className="col-span-3 font-medium">{log.source}</div>
                  <div className="col-span-6 text-slate-300">{log.message}</div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-20 text-slate-500">
                No logs matching current filters
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-2 border-t border-slate-700 flex justify-between items-center text-xs text-slate-400">
          <div>
            Showing {filteredLogs.length} of {simulationLogs.length} logs
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="h-7 px-2" onClick={clearLogs}>
              Clear Logs
            </Button>
            {/* <Button variant="ghost" size="sm" className="h-7 px-2">
              Auto-scroll
            </Button> */}
          </div>
        </div>
      </div>
    </div>
  )
}
