"use client"

import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { AIAgentsPanel } from "./ai-agents-panel"
import { ClickEventButton } from "@/helpers/components/butonEvent/clickEvent"
import { UserEventType } from "@/helpers/userEvents/userEvents.enums"

interface AIAgentsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AIAgentsModal({ isOpen, onClose }: AIAgentsModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
      <div className="bg-slate-900 border border-slate-700 rounded-lg w-[90vw] h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-3 border-b border-slate-700">
          <h2 className="text-lg font-medium">AI Agents</h2>
          <ClickEventButton eventType={UserEventType.AI_AGENT_CLOSE} elementType="button">
            <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
          </ClickEventButton>
        </div>
        <div className="flex-1 overflow-hidden">
          <AIAgentsPanel />
        </div>
      </div>
    </div>
  )
}
