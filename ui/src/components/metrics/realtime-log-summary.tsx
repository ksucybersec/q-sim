"use client"

import { useState, useEffect, useRef } from "react"
import { ChevronUp, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SocketEvents, WebSocketClient } from "@/services/socket"
import { RealtimeLogSummaryI } from "@/services/socket.interface"

interface TextLogSummaryProps {
    isSimulationRunning: boolean
    onMinimizedChange?: (isMinimized: boolean) => void
}

export function RealtimeLogSummary({ isSimulationRunning, onMinimizedChange }: TextLogSummaryProps) {
    const [isMinimized, setIsMinimized] = useState(false)
    const [summaryParts, setSummaryParts] = useState<string[]>([])
    const [displayedSummary, setDisplayedSummary] = useState<string>("")
    const [isUpdating, setIsUpdating] = useState(false)
    const [isTyping, setIsTyping] = useState(false)
    const scrollRef = useRef<HTMLDivElement>(null)
    const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
    const currentTypingIndex = useRef<number>(0)

    // Typewriter effect - display words one by one with race condition handling
    useEffect(() => {
        const fullSummary = summaryParts.join(' ')
        
        if (!fullSummary) {
            setDisplayedSummary("")
            setIsTyping(false)
            currentTypingIndex.current = 0
            return
        }

        if (fullSummary === displayedSummary) return

        setIsTyping(true)
        const words = fullSummary.split(' ')
        const currentWords = displayedSummary.split(' ')
        
        // Clear any existing timeout to handle race conditions
        if (typingTimeoutRef.current) {
            clearTimeout(typingTimeoutRef.current)
        }

        // Continue from where we left off, or start from beginning
        let wordIndex = currentWords.length === 1 && currentWords[0] === '' ? 0 : currentWords.length
        
        // If new content came in while typing, continue from current position
        if (wordIndex > words.length) {
            wordIndex = words.length
        }

        const typeNextWord = () => {
            if (wordIndex < words.length) {
                const newText = words.slice(0, wordIndex + 1).join(' ')
                setDisplayedSummary(newText)
                wordIndex++
                currentTypingIndex.current = wordIndex
                
                // Adjust typing speed (50-150ms per word)
                const delay = Math.random() * 100 + 50
                typingTimeoutRef.current = setTimeout(typeNextWord, delay)
            } else {
                setIsTyping(false)
                currentTypingIndex.current = wordIndex
            }
        }

        // Start typing after a brief delay
        typingTimeoutRef.current = setTimeout(typeNextWord, 100)

        return () => {
            if (typingTimeoutRef.current) {
                clearTimeout(typingTimeoutRef.current)
            }
        }
    }, [summaryParts])

    // Auto-scroll when displayed summary updates
    useEffect(() => {
        if (scrollRef.current && displayedSummary) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [displayedSummary])

    useEffect(() => {
        const handleLogMessage = (data: RealtimeLogSummaryI) => {
            console.log("Received log message:", data);
            
            // Handle both array and string cases for backward compatibility
            if (Array.isArray(data.summary_text)) {
                setSummaryParts(data.summary_text)
            } else {
                // If it's a string, treat it as a single part
                setSummaryParts([data.summary_text])
            }
        }

        if (!isSimulationRunning) {
            setSummaryParts([]);
            setDisplayedSummary('');
            setIsUpdating(false);
            setIsTyping(false);
            currentTypingIndex.current = 0;
            if (typingTimeoutRef.current) {
                clearTimeout(typingTimeoutRef.current);
            }
            WebSocketClient.getInstance().offMessage(SocketEvents.SimulationSummary, handleLogMessage);
        } else {
            setIsUpdating(true);
            WebSocketClient.getInstance().onMessage(SocketEvents.SimulationSummary, handleLogMessage);
        }

        // Cleanup function - always runs when effect re-runs or component unmounts
        return () => {
            WebSocketClient.getInstance().offMessage(SocketEvents.SimulationSummary, handleLogMessage);
            if (typingTimeoutRef.current) {
                clearTimeout(typingTimeoutRef.current);
            }
        };
    }, [isSimulationRunning]);

    return (
        <div className={isMinimized ? 'border-t border-slate-600 bg-slate-800' : 'h-45 border-t border-slate-600 bg-slate-800'}>
            {/* Header */}
            <div className="flex items-center justify-between p-3 bg-slate-750 h-48px">
                <div className="flex items-center space-x-2">
                    {(isUpdating || isTyping) && <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>}
                    <h3 className="text-sm font-semibold text-slate-200">Log Summary</h3>
                    {isTyping && <span className="text-xs text-slate-400">typing...</span>}
                    {summaryParts.length > 1 && (
                        <span className="text-xs text-slate-500">({summaryParts.length} parts)</span>
                    )}
                </div>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                        const newMinimized = !isMinimized
                        setIsMinimized(newMinimized)
                        onMinimizedChange?.(newMinimized)
                    }}
                    className="h-6 w-6 p-0 text-slate-400 hover:text-slate-200"
                >
                    {isMinimized ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </Button>
            </div>

            {/* Content */}
            {!isMinimized && (
                <div 
                    ref={scrollRef}
                    className="px-3 text-sm text-slate-300 leading-relaxed h-[calc(100%-48px)] overflow-y-auto scroll-smooth"
                >
                    {displayedSummary ? (
                        <>
                            {displayedSummary}
                            {isTyping && <span className="animate-pulse">|</span>}
                        </>
                    ) : (
                        <span className="text-gray-400 italic">**Logs will appear here.**</span>
                    )}
                </div>
            )}
        </div>
    )
}