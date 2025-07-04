"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Send, Plus, Atom, Zap } from "lucide-react"

// Monaco Editor imports
import { Editor, Monaco } from "@monaco-editor/react"
import { editor, Range } from 'monaco-editor';
import { ExerciseI } from "../labs/exercise /exercise"
import api from "@/services/api"
import { AgentID } from "../ai-agents/agent-declaration"
import { LabAssistantRequest } from "../ai-agents/message.interface"
import { LabAssistantResponse } from "@/services/apiResponse.interface"
import { toast } from "sonner"

import Markdown from 'react-markdown'


interface ChatMessage {
    id: string
    role: "user" | "assistant"
    content: string
}

const QUICK_PROMPTS = [
    "How do I create a Bell state?",
    "Show me a simple quantum circuit",
    "How to measure a qubit?",
    "Create entangled qubits",
    "Implement a Hadamard gate",
    "Visualize quantum states",
]

const SAMPLE_CODE = `# Quantum Network Simulator - QuTiP Example
import numpy as np
from qutip import *

# Create a qubit in superposition
psi = (basis(2, 0) + basis(2, 1)).unit()

# Apply Pauli-X gate
sigma_x = sigmax()
psi_new = sigma_x * psi

# Visualize the state
print("Initial state:", psi)
print("After X gate:", psi_new)

# Create entangled Bell state
bell_state = (tensor(basis(2,0), basis(2,0)) + 
              tensor(basis(2,1), basis(2,1))).unit()

print("Bell state created:", bell_state)
`
interface QuantumCodeEditorProps {
    activeLab: ExerciseI
}

export default function QuantumCodeEditor({ activeLab }: QuantumCodeEditorProps) {
    const [code, setCode] = useState(SAMPLE_CODE)
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const editorRef = useRef<editor.IStandaloneCodeEditor>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (!activeLab.coding) { return }
        setCode(activeLab.coding.scaffold.code)
        applyScaffoldSections();
    }, [activeLab])

    // Scroll to bottom of chat
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [messages])

    // const applyScaffoldSectionsBK = () => {
    //     if (!editorRef.current) {
    //         console.log('Editor not found')
    //         return;
    //     }
    //     const editorObj = editorRef.current;
    //     if (!activeLab?.coding?.scaffold?.sections?.length) return;
    //     const sections = activeLab.coding.scaffold.sections;

    //     // Get total line count
    //     const model = editorObj.getModel();
    //     if (!model) {
    //         console.log('Model not found')
    //         return;
    //     }
    //     const totalLines = model.getLineCount();

    //     // Create readonly ranges for everything EXCEPT editable sections
    //     const readonlyRanges: Range[] = [];
    //     let currentLine = 1;

    //     sections.forEach(section => {
    //         // Add readonly range before this editable section
    //         if (currentLine < section.startLine) {
    //             readonlyRanges.push(new Range(currentLine, 1, section.startLine - 1, Number.MAX_SAFE_INTEGER));
    //         }
    //         currentLine = section.endLine + 1;
    //     });

    //     // Add readonly range after last editable section
    //     if (currentLine <= totalLines) {
    //         readonlyRanges.push(new Range(currentLine, 1, totalLines, Number.MAX_SAFE_INTEGER));
    //     }

    //     // Prevent editing in readonly ranges
    //     editorObj.onKeyDown((e: any) => {
    //         const position = editorObj.getPosition();
    //         if (!position) return;
    //         const isInReadonlyRange = readonlyRanges.some(range => range.containsPosition(position));

    //         if (isInReadonlyRange && !e.ctrlKey && !e.metaKey) {
    //             e.preventDefault();
    //             e.stopPropagation();
    //         }
    //     });

    //     // Visual decorations for readonly sections
    //     const readonlyDecorations = readonlyRanges.map(range => ({
    //         range: range,
    //         options: {
    //             className: 'readonly-section',
    //             glyphMarginClassName: 'readonly-glyph'
    //         }
    //     }));

    //     editorObj.createDecorationsCollection(readonlyDecorations);

    //     // Collapse readonly sections
    //     readonlyRanges.forEach(range => {
    //         if (range.endLineNumber > range.startLineNumber) {
    //             editorObj.setSelection(range);
    //             const action = editorObj.getAction('editor.createFoldingRangeFromSelection')
    //             if (!action) {
    //                 console.log('Action not found')
    //             } else {
    //                 action.run()
    //             }
    //         }
    //     });
    // };

    const applyScaffoldSections = () => {
    if (!editorRef.current) {
        console.log('Editor not found');
        return;
    }
    
    const editorObj = editorRef.current;
    const model = editorObj.getModel();
    if (!model) {
        console.log('Model not found');
        return;
    }

    const content = model.getValue();
    const lines = content.split('\n');
    
    // Parse all functions and private variables
    const parsedSections = parsePythonCode(lines);
    
    // Get editable function names from lab config
    const editableFunctionNames = new Set(
        activeLab?.coding?.scaffold?.sections
            ?.filter(section => section.type === 'editable')
            ?.map(section => section.functionName) || []
    );

    // Create readonly ranges for all sections except editable functions
    const readonlyRanges: Range[] = [];
    
    parsedSections.forEach(section => {
        const isEditable = editableFunctionNames.has(section.name);
        
        if (!isEditable && section.type === 'function') {
            readonlyRanges.push(new Range(
                section.startLine, 
                1, 
                section.endLine, 
                Number.MAX_SAFE_INTEGER
            ));
        }
    });

    // Apply readonly behavior
    applyReadonlyBehavior(editorObj, readonlyRanges);
};

const parsePythonCode = (lines: string[]) => {
    const sections: Array<{
        type: 'function' | 'private_var' | 'other',
        name: string,
        startLine: number,
        endLine: number
    }> = [];

    let i = 0;
    while (i < lines.length) {
        const line = lines[i];
        const trimmedLine = line.trim();
        
        // Skip empty lines and comments
        if (!trimmedLine || trimmedLine.startsWith('#')) {
            i++;
            continue;
        }
        
        // Check for function definition
        const funcMatch = trimmedLine.match(/^def\s+(\w+)\s*\(/);
        if (funcMatch) {
            const functionName = funcMatch[1];
            const startLine = i + 1; // Monaco is 1-indexed
            const endLine = findFunctionEnd(lines, i);
            
            sections.push({
                type: 'function',
                name: functionName,
                startLine,
                endLine
            });
            
            i = endLine; // Jump to end of function
            continue;
        }
        
        // Check for private class variables (self._variable = ...)
        const privateVarMatch = trimmedLine.match(/^self\.(_\w+)\s*=/);
        if (privateVarMatch) {
            sections.push({
                type: 'private_var',
                name: privateVarMatch[1],
                startLine: i + 1,
                endLine: i + 1
            });
        }
        
        i++;
    }

    // Handle any remaining code (imports, class definitions, etc.)
    let currentLine = 1;
    const functionRanges = sections
        .filter(s => s.type === 'function')
        .sort((a, b) => a.startLine - b.startLine);

    functionRanges.forEach(func => {
        if (currentLine < func.startLine) {
            // Code before this function (imports, class def, etc.)
            sections.push({
                type: 'other',
                name: 'header_code',
                startLine: currentLine,
                endLine: func.startLine - 1
            });
        }
        currentLine = func.endLine + 1;
    });

    // Code after last function
    if (currentLine <= lines.length) {
        sections.push({
            type: 'other',
            name: 'footer_code',
            startLine: currentLine,
            endLine: lines.length
        });
    }

    return sections;
};

const findFunctionEnd = (lines: string[], startIndex: number): number => {
    const functionLine = lines[startIndex];
    const functionIndent = functionLine.search(/\S/); // Find indentation level
    
    let lastCodeLine = startIndex;
    
    // Look for the end of the function
    for (let i = startIndex + 1; i < lines.length; i++) {
        const line = lines[i];
        const trimmedLine = line.trim();
        
        // Empty line - continue but don't update lastCodeLine
        if (trimmedLine === '') {
            continue;
        }
        
        const lineIndent = line.search(/\S/);
        
        // Comment at function level or less - function ends here
        if (trimmedLine.startsWith('#') && lineIndent <= functionIndent) {
            return lastCodeLine + 1;
        }
        
        // Comment inside function - continue
        if (trimmedLine.startsWith('#') && lineIndent > functionIndent) {
            continue;
        }
        
        // Code at function level or less - function ends here
        if (lineIndent !== -1 && lineIndent <= functionIndent) {
            return lastCodeLine + 1;
        }
        
        // Code inside function - update lastCodeLine
        if (lineIndent > functionIndent) {
            lastCodeLine = i;
        }
    }
    
    // Function goes to end of file
    return lastCodeLine + 1;
};

const applyReadonlyBehavior = (editorObj: editor.IStandaloneCodeEditor, readonlyRanges: Range[]) => {
    // Prevent editing in readonly ranges
    editorObj.onKeyDown((e: any) => {
        const position = editorObj.getPosition();
        if (!position) return;
        
        const isInReadonlyRange = readonlyRanges.some(range => 
            range.containsPosition(position)
        );

        if (isInReadonlyRange && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            e.stopPropagation();
        }
    });

    // Visual decorations for readonly sections
    const readonlyDecorations = readonlyRanges.map(range => ({
        range: range,
        options: {
            className: 'readonly-section',
            glyphMarginClassName: 'readonly-glyph'
        }
    }));

    editorObj.createDecorationsCollection(readonlyDecorations);
    console.log(editorObj)

    // Collapse readonly sections
    readonlyRanges.forEach(async (range) => {
        if (range.endLineNumber > range.startLineNumber) {
            console.log('Collapsing range:', range);
            editorObj.setSelection(range);
            const action = editorObj.getAction('editor.fold');
            editorObj.setPosition({lineNumber: range.startLineNumber, column: 10});
            if (action) {
                console.log(action)
                await action.run({
                    levels: 2,
                    direction: 'down',
                    selectionLines: [range.startLineNumber],
                });
            } else {
                console.error('Failed to create folding range from selection');
            }
        }
    });
};

    const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
        editorRef.current = editor

        // Configure Monaco theme for quantum aesthetic
        monaco.editor.defineTheme('quantum-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'comment', foreground: '6B7280', fontStyle: 'italic' },
                { token: 'keyword', foreground: '60A5FA' },
                { token: 'string', foreground: '34D399' },
                { token: 'number', foreground: 'F59E0B' },
                { token: 'function', foreground: 'A78BFA' },
            ],
            colors: {
                'editor.background': '#0F172A',
                'editor.foreground': '#F1F5F9',
                'editor.lineHighlightBackground': '#1E293B',
                'editor.selectionBackground': '#3B82F650',
                'editorLineNumber.foreground': '#64748B',
                'editorLineNumber.activeForeground': '#94A3B8',
            }
        })

        monaco.editor.setTheme('quantum-dark')


        // Configure editor options
        editor.updateOptions({
            fontSize: window.innerWidth < 640 ? 12 : 14,
            lineHeight: window.innerWidth < 640 ? 20 : 24,
            minimap: { enabled: window.innerWidth >= 1024 },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            folding: true,
            lineNumbers: 'on',
            glyphMargin: true,
        })

        applyScaffoldSections()
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInput(e.target.value)
    }
    
    const replaceFunctionInCode = (functionName: string, generatedCode: string, startLineNumber: number) => {
        if (!editorRef.current) return
     
        const editor = editorRef.current
        const model = editor.getModel()
        if (!model) return
     
        const totalLines = model.getLineCount()
        let actualStartLine = null
        let endLineNumber = totalLines
     
        // First, verify the function exists at the given line number
        const lineAtGivenNumber = model.getLineContent(startLineNumber).trim()
        if (lineAtGivenNumber.includes(`def ${functionName}(`)) {
            actualStartLine = startLineNumber
        } else {
            // Search for the function throughout the file
            for (let i = 1; i <= totalLines; i++) {
                const lineContent = model.getLineContent(i).trim()
                if (lineContent.includes(`def ${functionName}(`)) {
                    actualStartLine = i
                    break
                }
            }
        }
     
        // If function not found, insert at the end of the class or file
        if (!actualStartLine) {
            // Find last line of the class (look for class indentation level)
            let insertLine = totalLines
            for (let i = totalLines; i >= 1; i--) {
                const lineContent = model.getLineContent(i)
                if (lineContent.trim() && !lineContent.startsWith(' ') && !lineContent.startsWith('\t')) {
                    insertLine = i + 1
                    break
                }
            }
     
            // Insert new function
            const range = new Range(insertLine, 1, insertLine, 1)
            editor.executeEdits("insert-function", [
                {
                    range: range,
                    text: '\n' + generatedCode + '\n'
                }
            ])
     
            editor.focus()
            editor.setPosition({ lineNumber: insertLine + 1, column: 1 })
            return
        }
     
        // Find the end of the existing function
        const functionIndentation = model.getLineContent(actualStartLine).search(/\S/)
        
        for (let i = actualStartLine + 1; i <= totalLines; i++) {
            const lineContent = model.getLineContent(i)
            
            // Skip empty lines
            if (!lineContent.trim()) continue
            
            const currentIndentation = lineContent.search(/\S/)
            
            // If we find a line with same or less indentation than function def, function ends
            if (currentIndentation !== -1 && currentIndentation <= functionIndentation) {
                endLineNumber = i - 1
                break
            }
        }
     
        // Replace the existing function
        const range = new Range(
            actualStartLine,
            1,
            endLineNumber,
            model.getLineMaxColumn(endLineNumber)
        )
     
        editor.executeEdits("replace-function", [
            {
                range: range,
                text: generatedCode
            }
        ])
     
        editor.focus()
        editor.setPosition({ lineNumber: actualStartLine, column: 1 })
     }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || isLoading) return

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            role: "user",
            content: input.trim(),
        }

        const newMessages = [...messages, userMessage]
        setMessages(newMessages)
        setInput("")
        setIsLoading(true)

        try {
            const position = editorRef.current?.getPosition();
            if (!position) { return }

            const request: LabAssistantRequest = {
                agent_id: AgentID.LAB_ASSISTANT_AGENT,
                conversation_id: "1",
                user_query: userMessage.content,
                cursor_line_number: position.lineNumber,
                student_code: code,
            }
            const response: LabAssistantResponse = await api.sendAgentMessage(request)

            if (!response) {
                throw new Error("Failed to get response")
            }

            // Handle Response
            replaceFunctionInCode( response.function_name, response.generated_code, response.start_line_number)

            const assistantMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: response.explanation,
            }

            setMessages((prev) => [
                ...prev,
                assistantMessage,
            ])

            toast.success(`Function "${response.function_name}" updated!`)
        } catch (error) {
            console.error("Error:", error)
            setMessages((prev) => [
                ...prev,
                {
                    id: (Date.now() + 1).toString(),
                    role: "assistant",
                    content: "Sorry, I encountered an error. Please try again.",
                },
            ])
        } finally {
            setIsLoading(false)
        }
    }

    const handleQuickPrompt = (prompt: string) => {
        setInput(prompt)
    }

    const insertCodeAtCursor = (codeSnippet: string) => {
        if (!editorRef.current) return

        const editor = editorRef.current
        const selection = editor.getSelection()
        const position = editor.getPosition();
        if (!position) { return }
        const range = selection || {
            startLineNumber: position.lineNumber,
            startColumn: position.column,
            endLineNumber: position.lineNumber,
            endColumn: position.column,
        }

        editor.executeEdits("insert-code", [
            {
                range: range,
                text: codeSnippet,
            },
        ])

        editor.focus()
    }

    const extractCodeFromMessage = (content: string) => {
        const codeBlocks = content.match(/```python\n([\s\S]*?)\n```/g)
        return codeBlocks ? codeBlocks.map((block) => block.replace(/```python\n/, "").replace(/\n```/, "")) : []
    }

    return (
        <div className="w-full h-full bg-slate-900 text-slate-100 flex flex-col">
            <ResizablePanelGroup direction="vertical" className="flex-1 min-h-0">
                {/* Code Editor Panel */}
                <ResizablePanel defaultSize={60} minSize={30} className="flex flex-col">
                    <div className="flex flex-col h-full bg-slate-900">
                        {/* Code Editor Header */}
                        <div className="flex items-center justify-between p-2 sm:p-3 border-b border-slate-700 bg-slate-800/30 flex-shrink-0">
                            <div className="flex items-center gap-2">
                                <Atom className="w-4 h-4 text-blue-400" />
                                <span className="text-sm font-medium hidden sm:inline">Quantum Code Editor</span>
                                <span className="text-xs font-medium sm:hidden">Code</span>
                                <Badge variant="outline" className="text-xs border-blue-500 text-blue-400 hidden sm:inline-flex">
                                    Python/QuTiP
                                </Badge>
                            </div>
                        </div>

                        {/* Monaco Editor */}
                        <div className="flex-1 min-h-0">
                            <Editor
                                height="100%"
                                defaultLanguage="python"
                                value={code}
                                onChange={(value) => setCode(value || "")}
                                onMount={handleEditorDidMount}
                                options={{
                                    automaticLayout: true,
                                    scrollBeyondLastLine: false,
                                    wordWrap: 'on',
                                    minimap: { enabled: false },
                                    fontSize: 14,
                                    lineHeight: 24,
                                    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                                    padding: { top: 16, bottom: 16 },
                                    folding: true,
                                    lineNumbers: 'on',
                                    glyphMargin: true,
                                    renderLineHighlight: 'line',
                                    cursorBlinking: 'smooth',
                                    smoothScrolling: true,
                                }}
                                loading={
                                    <div className="flex items-center justify-center h-full bg-slate-900 text-slate-400">
                                        <div className="animate-spin w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full mr-3"></div>
                                        Loading Editor...
                                    </div>
                                }
                            />
                        </div>
                    </div>
                </ResizablePanel>

                <ResizableHandle className="bg-slate-700 hover:bg-slate-600 transition-colors" />

                {/* AI Chat Panel */}
                <ResizablePanel defaultSize={40} minSize={25} className="flex flex-col">
                    <div className="flex flex-col h-full bg-slate-800/50">
                        {/* Chat Header */}
                        <div className="flex items-center gap-2 p-2 sm:p-3 border-b border-slate-700 bg-slate-800/50 flex-shrink-0">
                            <Zap className="w-4 h-4 text-yellow-400" />
                            <span className="text-sm font-medium">Quantum AI Assistant</span>
                            {/* <Badge variant="outline" className="text-xs border-green-500 text-green-400">
                                Online
                            </Badge> */}
                        </div>

                        {/* Quick Prompts */}
                        <div className="p-2 sm:p-3 border-b border-slate-700 flex-shrink-0">
                            <div className="text-xs text-slate-400 mb-2">Quick prompts:</div>
                            <div className="flex flex-wrap gap-1">
                                {(activeLab?.coding?.aiPrompts || QUICK_PROMPTS).slice(0, window.innerWidth < 640 ? 2 : 3).map((prompt, index) => (
                                    <Button
                                        key={index}
                                        variant="outline"
                                        size="sm"
                                        className="text-xs h-6 border-slate-600 hover:border-blue-500 hover:text-blue-400 bg-transparent"
                                        onClick={() => handleQuickPrompt(prompt)}
                                    >
                                        <span className="truncate max-w-[120px] sm:max-w-none">{prompt}</span>
                                    </Button>
                                ))}
                            </div>
                        </div>

                        {/* Chat Messages */}
                        <div className="flex-1 min-h-0">
                            <ScrollArea className="h-full">
                                <div className="p-2 sm:p-3 space-y-3 sm:space-y-4">
                                    {messages.length === 0 && (
                                        <div className="text-center text-slate-400 py-4 sm:py-8">
                                            <Atom className="w-6 h-6 sm:w-8 sm:h-8 mx-auto mb-2 text-blue-400" />
                                            <p className="text-xs sm:text-sm">Ask me anything about quantum programming!</p>
                                            <p className="text-xs mt-1 hidden sm:block">
                                                I can help with QuTiP, Qiskit, and quantum concepts.
                                            </p>
                                        </div>
                                    )}

                                    {messages.map((message) => (
                                        <div
                                            key={message.id}
                                            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                                        >
                                            <div
                                                className={`max-w-[85%] sm:max-w-[80%] rounded-lg p-2 sm:p-3 ${message.role === "user" ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-100"
                                                    }`}
                                            >
                                                <div className="text-xs sm:text-sm whitespace-pre-wrap break-words"><Markdown>{message.content}</Markdown></div>

                                                {/* Code extraction and insertion */}
                                                {message.role === "assistant" && extractCodeFromMessage(message.content).length > 0 && (
                                                    <div className="mt-2 pt-2 border-t border-slate-600">
                                                        {extractCodeFromMessage(message.content).map((codeBlock, index) => (
                                                            <Button
                                                                key={index}
                                                                variant="outline"
                                                                size="sm"
                                                                className="text-xs mr-2 mb-1 border-slate-500 hover:border-green-500 hover:text-green-400 bg-transparent h-6"
                                                                onClick={() => insertCodeAtCursor(codeBlock)}
                                                            >
                                                                <Plus className="w-3 h-3 mr-1" />
                                                                <span className="hidden sm:inline">Insert Code</span>
                                                                <span className="sm:hidden">Insert</span>
                                                            </Button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}

                                    {isLoading && (
                                        <div className="flex justify-start">
                                            <div className="bg-slate-700 rounded-lg p-2 sm:p-3 max-w-[80%]">
                                                <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-300">
                                                    <div className="animate-spin w-3 h-3 sm:w-4 sm:h-4 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                                                    <span className="hidden sm:inline">Thinking about quantum mechanics...</span>
                                                    <span className="sm:hidden">Thinking...</span>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    <div ref={messagesEndRef} />
                                </div>
                            </ScrollArea>
                        </div>

                        {/* Chat Input */}
                        <div className="p-2 sm:p-3 border-t border-slate-700 flex-shrink-0">
                            <div className="flex gap-2">
                                <Input
                                    value={input}
                                    onChange={handleInputChange}
                                    placeholder="Ask about quantum programming..."
                                    className="flex-1 bg-slate-800 border-slate-600 text-slate-100 placeholder-slate-400 text-xs sm:text-sm h-8 sm:h-10"
                                    disabled={isLoading}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault()
                                            handleSubmit(e)
                                        }
                                    }}
                                />
                                <Button
                                    onClick={handleSubmit}
                                    disabled={isLoading || !input.trim()}
                                    className="bg-blue-600 hover:bg-blue-700 h-8 sm:h-10 px-2 sm:px-4"
                                    size="sm"
                                >
                                    <Send className="w-3 h-3 sm:w-4 sm:h-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    )
}