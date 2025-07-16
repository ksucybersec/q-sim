"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { MessageCircle, X, Send, User, Bot } from "lucide-react"
import { ChatRequestI, LabPeerAgentInput, LabPeerAgentOutput } from "../message.interface"
import { uniqueId } from "lodash"
import { AgentID, AgentTask } from "../agent-declaration"
import api from "@/services/api"
import { ExerciseI } from "@/components/labs/exercise /exercise"
import { exportToJSON } from "@/services/exportService"
import { ClickEventButton } from "@/helpers/components/butonEvent/clickEvent"
import { UserEventType } from "@/helpers/userEvents/userEvents.enums"
import { sendAIAgentMessageSentEvent, sendAiAgentResponseReceivedEvent } from "@/helpers/userEvents/userEvents"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface LabPeerChatBotProps {
  activeLab: ExerciseI
}

export default function LabPeerChatbot({ activeLab }: LabPeerChatBotProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hey there! 👋 I'm your lab peer - here to help you work through any tricky quantum networking problems or concepts. What are you working on today?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [conversationID, setConversationID] = useState<string>(uniqueId(Date.now().toString()));

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Replace this with your AI implementation
      const aiResponse = await sendMessageToAI(input.trim(), messages)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResponse.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I'm having trouble responding right now. Can you try again?",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }
  const sendMessageToAI = async (message: string, chatHistory: Message[]) => {
    const request: LabPeerAgentInput = {
      conversation_id: conversationID,
      agent_id: AgentID.LAB_ASSISTANT_AGENT,
      user_query: message,
      task_id: AgentTask.LAB_PEER,
      lab_instructions: activeLab,
      current_topology: exportToJSON()
    }

    sendAIAgentMessageSentEvent(request)
    const response = await api.sendAgentMessage<LabPeerAgentOutput>(request)
    sendAiAgentResponseReceivedEvent(response, request)

    return response
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  const toggleChat = () => setIsOpen(!isOpen)

  const clearChat = () => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "Hey there! 👋 I'm your lab peer - here to help you work through any tricky quantum networking problems or concepts. What are you working on today?",
        timestamp: new Date(),
      },
    ])
  }

  return (
    <>
      {/* Floating Action Button */}
      <ClickEventButton eventType={isOpen ? UserEventType.AI_AGENT_CLOSE : UserEventType.AI_AGENT_OPEN} elementDescription="Clicked Lab Peer Chatbot" elementType="Lab Peer Chat Bot Box Button">
        <Button
          onClick={toggleChat}
          className={`fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg transition-all duration-300 z-50 border-2 ${isOpen
            ? "bg-slate-700 hover:bg-slate-600 border-slate-500 text-white"
            : "bg-violet-600 hover:bg-violet-700 border-violet-500 text-white"
            }`}
          size="icon"
          aria-label={isOpen ? "Close chat" : "Open chat"}
        >
          {isOpen ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
        </Button>
      </ClickEventButton>

      {/* Chat Window */}
      {isOpen && (
        <Card className="fixed bottom-24 right-6 w-96 h-[500px] shadow-2xl z-40 flex flex-col animate-in slide-in-from-bottom-2 duration-300 bg-slate-800 border-slate-600 py-0  overflow-hidden">
          <CardHeader className="bg-slate-700 text-white rounded-t-lg py-3 border-b border-slate-600">
            <CardTitle className="text-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-violet-400" />
                <span className="text-violet-200">Lab Peer Assistant</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearChat}
                className="text-slate-300 hover:bg-slate-600 hover:text-white h-8 w-8 p-0"
                aria-label="Clear chat"
              >
                <X className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0 bg-slate-800 rounded-xl min-h-0">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start gap-3 ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                >
                  <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${message.role === "user" ? "bg-violet-600 text-white" : "bg-slate-600 text-slate-200"
                      }`}
                  >
                    {message.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${message.role === "user"
                      ? "bg-violet-600 text-white rounded-br-none"
                      : "bg-slate-700 text-slate-100 rounded-bl-none border border-slate-600"
                      }`}
                  >
                    <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                    <div
                      className={`text-xs mt-1 opacity-70 ${message.role === "user" ? "text-violet-200" : "text-slate-400"
                        }`}
                    >
                      {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-600 text-slate-200 flex items-center justify-center">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-slate-700 p-3 rounded-lg rounded-bl-none border border-slate-600">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-violet-400 rounded-full animate-bounce"></div>
                      <div
                        className="w-2 h-2 bg-violet-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-2 h-2 bg-violet-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-slate-600 p-4 bg-slate-800 rounded-xl flex-shrink-0">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Ask your lab peer anything..."
                  className="flex-1 bg-slate-700 border-slate-600 text-slate-100 placeholder:text-slate-400 focus:border-violet-500 focus:ring-violet-500"
                  disabled={isLoading}
                  maxLength={500}
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={isLoading || !input.trim()}
                  className="bg-violet-600 hover:bg-violet-700 border-violet-500"
                  aria-label="Send message"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </form>
              <div className="text-xs text-slate-400 mt-1">{input.length}/500 characters</div>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  )
}
