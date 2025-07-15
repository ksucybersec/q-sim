"use client"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, Info, Search, BookOpen, GitBranch, Network, ChevronDown, Activity } from "lucide-react"
import { WebSocketClient } from "@/services/socket"
import { convertEventToLog } from "./log-parser"
import { Input } from "../ui/input"
import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuTrigger } from "../ui/dropdown-menu"

const animationStyles = `
  @keyframes slideInFromTop {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes pulseGlow {
    0%, 100% {
      box-shadow: 0 0 0 0 currentColor;
    }
    50% {
      box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3);
    }
  }
  
  @keyframes activityPulse {
    0%, 100% {
      opacity: 0.4;
      transform: scale(1);
    }
    50% {
      opacity: 0.8;
      transform: scale(1.05);
    }
  }
  
  @keyframes slideInActivity {
    from {
      opacity: 0;
      transform: translateX(-10px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  .log-enter {
    animation: slideInFromTop 0.4s ease-out;
  }
  
  .recent-log {
    animation: pulseGlow 2s ease-in-out;
  }
  
  .activity-pulse {
    animation: activityPulse 1.5s ease-in-out infinite;
  }
  
  .activity-enter {
    animation: slideInActivity 0.3s ease-out;
  }
`

export enum LogLevel {
  STORY = 1, // High-level narrative: What happened?
  PROTOCOL = 2, // Detailed steps: How did it happen?
  NETWORK = 3, // Verbose mechanics: The nitty-gritty details.
  WARN = 4,
  ERROR = 5,
}

export interface LogI {
  level: LogLevel
  time: string
  source: string
  message: string
}

interface SourceActivity {
  source: string
  lastSeen: number
  level: LogLevel
}

export function SimulationLogsPanel() {
  // Add this right at the start of the component
  useEffect(() => {
    const styleSheet = document.createElement("style")
    styleSheet.textContent = animationStyles
    document.head.appendChild(styleSheet)
    return () => {
      document.head.removeChild(styleSheet)
    }
  }, [])

  const socket = WebSocketClient.getInstance()
  const [logFilter, setLogFilter] = useState<LogLevel[]>([LogLevel.STORY, LogLevel.PROTOCOL, LogLevel.ERROR])
  const [searchQuery, setSearchQuery] = useState("")
  const [simulationLogs, setSimulationLogs] = useState<LogI[]>(
    socket.simulationEventLogs
      .reverse()
      .map((x) => convertEventToLog(x))
      .filter((x) => x !== undefined),
  )
  const [filteredLogs, setFilteredLogs] = useState<LogI[]>(simulationLogs)
  const [recentLogIds, setRecentLogIds] = useState<Set<string>>(new Set())
  const [recentActivity, setRecentActivity] = useState<SourceActivity[]>([])

  useEffect(() => {
    const handleEvent = (event: any) => {
      const converted = convertEventToLog(event)
      if (converted) {
        // Create a unique ID for this log entry
        const logId = `${converted.time}-${converted.source}-${Date.now()}`

        setSimulationLogs((prevLogs) => {
          const newLogs = [converted, ...prevLogs]
          return newLogs
        })

        // Update recent activity tracker
        setRecentActivity((prevActivity) => {
          const now = Date.now()
          const newActivity: SourceActivity = {
            source: converted.source,
            lastSeen: now,
            level: converted.level,
          }

          // Remove old activity (older than 10 seconds) and update existing or add new
          const filtered = prevActivity.filter((activity) => now - activity.lastSeen < 10000)
          const existingIndex = filtered.findIndex((activity) => activity.source === converted.source)

          if (existingIndex >= 0) {
            filtered[existingIndex] = newActivity
          } else {
            filtered.unshift(newActivity)
          }

          // Keep only the 8 most recent sources
          return filtered.slice(0, 8)
        })

        // Mark this log as recent using its unique ID
        setRecentLogIds((prev) => new Set([...prev, logId]))

        // Remove the recent status after 3 seconds
        setTimeout(() => {
          setRecentLogIds((prev) => {
            const updated = new Set(prev)
            updated.delete(logId)
            return updated
          })
        }, 3000)
      }
    }

    socket.onMessage("simulation_event", handleEvent)
    return () => {
      socket.offMessage("simulation_event", handleEvent)
    }
  }, [])

  useEffect(() => {
    updateFilteredLogs()
  }, [logFilter, searchQuery, simulationLogs])

  const updateFilteredLogs = () => {
    const filterQuery = simulationLogs.filter((log) => {
      const matchesLevel = logFilter.length === 0 || logFilter.includes(log.level)
      const matchesSearch =
        searchQuery === "" ||
        log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.source.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesLevel && matchesSearch
    })
    setFilteredLogs(filterQuery)
  }

  const getLogLevelIcon = (level: LogLevel) => {
    switch (level) {
      case LogLevel.STORY:
        return <BookOpen className="h-4 w-4" />
      case LogLevel.PROTOCOL:
        return <GitBranch className="h-4 w-4" />
      case LogLevel.NETWORK:
        return <Network className="h-4 w-4" />
      case LogLevel.WARN:
        return <AlertTriangle className="h-4 w-4" />
      case LogLevel.ERROR:
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <Info className="h-4 w-4" />
    }
  }

  const getLogLevelStyles = (level: LogLevel) => {
    switch (level) {
      case LogLevel.STORY:
        return {
          dot: "bg-green-500 border-green-400",
          line: "bg-green-500/20",
          card: "border-green-500/20 bg-green-500/5",
          text: "text-green-400",
          activity: "bg-green-500/30",
        }
      case LogLevel.PROTOCOL:
        return {
          dot: "bg-blue-500 border-blue-400",
          line: "bg-blue-500/20",
          card: "border-blue-500/20 bg-blue-500/5",
          text: "text-blue-400",
          activity: "bg-blue-500/30",
        }
      case LogLevel.NETWORK:
        return {
          dot: "bg-slate-500 border-slate-400",
          line: "bg-slate-500/20",
          card: "border-slate-500/20 bg-slate-500/5",
          text: "text-slate-400",
          activity: "bg-slate-500/30",
        }
      case LogLevel.WARN:
        return {
          dot: "bg-amber-500 border-amber-400",
          line: "bg-amber-500/20",
          card: "border-amber-500/20 bg-amber-500/5",
          text: "text-amber-400",
          activity: "bg-amber-500/30",
        }
      case LogLevel.ERROR:
        return {
          dot: "bg-red-500 border-red-400",
          line: "bg-red-500/20",
          card: "border-red-500/20 bg-red-500/5",
          text: "text-red-400",
          activity: "bg-red-500/30",
        }
      default:
        return {
          dot: "bg-gray-500 border-gray-400",
          line: "bg-gray-500/20",
          card: "border-gray-500/20 bg-gray-500/5",
          text: "text-gray-400",
          activity: "bg-gray-500/30",
        }
    }
  }

  const clearLogs = () => {
    setSimulationLogs([])
    socket.simulationEventLogs = []
    setRecentActivity([])
  }

  const onFilterChange = (checked: boolean, levelStr: string) => {
    const level = LogLevel[levelStr as keyof typeof LogLevel]
    if (checked && !logFilter.includes(level)) {
      setLogFilter((prev) => [...prev, level])
    } else if (!checked && logFilter.includes(level)) {
      setLogFilter((prev) => prev.filter((l) => l !== level))
    }
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Simulator Timeline</h3>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="secondary" size="sm">
              <ChevronDown className="h-3 w-3" />
              Log Level
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {Object.keys(LogLevel)
              .filter((key) => isNaN(key as any))
              .map((levelStr) => (
                <DropdownMenuCheckboxItem
                  key={levelStr}
                  checked={logFilter.includes(LogLevel[levelStr as keyof typeof LogLevel])}
                  onCheckedChange={(checked) => onFilterChange(checked, levelStr)}
                >
                  {levelStr}
                </DropdownMenuCheckboxItem>
              ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Subtle Activity Indicator */}
      {recentActivity.length > 0 && (
        <div className="bg-slate-800/50 rounded-md border border-slate-700/50 px-3 py-2">
          <div className="flex items-center gap-2">
            <Activity className="h-3 w-3 text-slate-400" />
            <span className="text-xs text-slate-400">Recent Activity:</span>
            <div className="flex items-center gap-1 overflow-hidden">
              {recentActivity.slice(0, 6).map((activity, idx) => {
                const styles = getLogLevelStyles(activity.level)
                const isVeryRecent = Date.now() - activity.lastSeen < 2000

                return (
                  <div key={`${activity.source}-${idx}`} className="flex items-center gap-1 activity-enter">
                    <div
                      className={`h-2 w-2 rounded-full ${styles.activity} ${isVeryRecent ? "activity-pulse" : ""}`}
                      title={activity.source}
                    />
                    <span className="text-xs text-slate-500 truncate max-w-20">
                      {activity.source.split("-").pop() || activity.source}
                    </span>
                    {idx < Math.min(recentActivity.length - 1, 5) && <span className="text-slate-600 text-xs">→</span>}
                  </div>
                )
              })}
              {recentActivity.length > 6 && (
                <span className="text-xs text-slate-500">+{recentActivity.length - 6}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <Input
          placeholder="Search timeline..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Timeline Container */}
      <div className="bg-slate-900 rounded-lg border border-slate-700 flex-1 min-h-0 overflow-hidden">
        <div className="h-full overflow-auto">
          <div className="p-3">
            {filteredLogs.length > 0 ? (
              <div className="relative">
                {/* Timeline Line */}
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700"></div>

                {/* Timeline Items */}
                <div className="space-y-2">
                  {filteredLogs.map((log, idx) => {
                    const styles = getLogLevelStyles(log.level)
                    const logId = `${log.time}-${log.source}-${idx}`
                    const isRecent = recentLogIds.has(logId) || idx === 0 // First item is always most recent

                    return (
                      <div key={logId} className={`relative flex items-start gap-3 ${isRecent ? "log-enter" : ""}`}>
                        {/* Timeline Dot - Add recent animation */}
                        <div
                          className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full border ${styles.dot} flex-shrink-0 ${isRecent ? "recent-log" : ""}`}
                        >
                          <div className={`${styles.text} scale-75`}>{getLogLevelIcon(log.level)}</div>
                        </div>

                        {/* Content - Add subtle highlight for recent logs */}
                        <div
                          className={`flex-1 rounded border px-3 py-2 ${styles.card} min-w-0 ${isRecent ? "ring-1 ring-blue-500/30" : ""} transition-all duration-300`}
                        >
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <div className="flex items-center gap-2 min-w-0">
                              <Badge
                                variant="outline"
                                className={`${styles.text} border-current text-xs px-1.5 py-0.5 flex-shrink-0`}
                              >
                                {LogLevel[log.level]}
                              </Badge>
                              <span className="text-xs font-medium text-slate-300 truncate">{log.source}</span>
                            </div>
                            <time className="text-xs font-mono text-slate-400 flex-shrink-0">{log.time}</time>
                          </div>
                          <p className="text-sm text-slate-200 leading-snug">{log.message}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-slate-500">
                <div className="text-center">
                  <div className="text-base font-medium mb-1">No events in timeline</div>
                  <div className="text-sm">Adjust your filters or wait for new events</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-700 px-4 py-2 flex justify-between items-center text-sm text-slate-400 flex-shrink-0">
          <div>
            {filteredLogs.length > 0 && (
              <span>
                Showing {filteredLogs.length} of {simulationLogs.length} events
              </span>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={clearLogs} className="text-slate-400 hover:text-slate-200 h-7">
            Clear Timeline
          </Button>
        </div>
      </div>
    </div>
  )
}
