"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Send, Bot, User, Trash2, AlertCircle } from "lucide-react"
import {
    getChatMessages,
    saveChatMessages,
    completePendingRequest,
    hasPendingRequest,
    sendChatMessage,
    ChatMessage
} from "@/lib/chat-service"

const CHAT_STORAGE_KEY = "io-guard-chat-messages"

export default function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [input, setInput] = useState("")
    const [loading, setLoading] = useState(false)
    const [pendingCheck, setPendingCheck] = useState(false)
    const chatEndRef = useRef<HTMLDivElement>(null)

    // Model Selection State
    const [models, setModels] = useState<any[]>([])
    const [selectedModel, setSelectedModel] = useState<string>("")
    const [loadingModels, setLoadingModels] = useState(true)

    // Load messages and check for pending requests on mount
    useEffect(() => {
        const loadedMessages = getChatMessages()
        setMessages(loadedMessages)

        // Check if there's a pending request from before navigation
        if (hasPendingRequest()) {
            setLoading(true) // Restore loading state immediately
            setPendingCheck(true)

            completePendingRequest().then((response) => {
                if (response) {
                    // Reload messages which now include the response
                    setMessages(getChatMessages())
                }
                setPendingCheck(false)
                setLoading(false) // Clear loading state only after completion
            })
        }
    }, [])

    // Fetch models on mount
    useEffect(() => {
        const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        fetch(`${NEXT_PUBLIC_API_URL}/v1/models`)
            .then(res => res.json())
            .then(data => {
                setModels(data.models)
                // Default if not already set (maybe persist later)
                if (!selectedModel) setSelectedModel(data.default_model)
                setLoadingModels(false)
            })
            .catch(err => {
                console.error("Failed to fetch models:", err)
                setLoadingModels(false)
            })
    }, [])

    // Save messages to sessionStorage on change
    useEffect(() => {
        if (messages.length > 0) {
            saveChatMessages(messages)
        }
    }, [messages])

    // Scroll to bottom on new messages
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [messages])

    const clearChat = () => {
        sessionStorage.removeItem(CHAT_STORAGE_KEY)
        setMessages([{ role: "assistant", content: "Chat temizlendi. Size nasıl yardımcı olabilirim?" }])
    }

    const handleSend = async () => {
        if (!input.trim()) return

        const userMsg: ChatMessage = { role: "user", content: input }
        const updatedMessages = [...messages, userMsg]
        setMessages(updatedMessages)
        setInput("")
        setLoading(true)

        // Use the chat service which handles background requests
        await sendChatMessage(
            messages,
            userMsg,
            (response) => {
                setMessages(prev => [...prev, response])
                setLoading(false)
            },
            (error) => {
                setMessages(prev => [...prev, { role: "assistant", content: `Error: ${error}` }])
                setLoading(false)
            },
            selectedModel // Pass selected model
        )
    }


    return (
        <div className="h-full p-8 flex flex-col space-y-4">
            <h2 className="text-3xl font-bold tracking-tight">io Intelligence</h2>

            <Card className="flex-1 flex flex-col min-h-[500px]">
                <CardHeader className="border-b">
                    <CardTitle className="flex items-center justify-between text-lg">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center">
                                <Bot className="mr-2 h-5 w-5 text-purple-500" />
                                AI Agent
                            </div>

                            {/* Model Selector */}
                            <select
                                className="h-7 bg-purple-500/10 text-purple-500 border-none rounded-full px-3 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-purple-500 cursor-pointer"
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                                disabled={loadingModels || loading}
                            >
                                {models.length > 0 ? (
                                    models.map(m => (
                                        <option key={m.id} value={m.id}>
                                            {m.name}
                                        </option>
                                    ))
                                ) : (
                                    <option>Loading Models...</option>
                                )}
                            </select>

                            {messages.length > 1 && (
                                <span className="ml-2 text-xs text-zinc-500">
                                    ({messages.length} mesaj)
                                </span>
                            )}
                        </div>
                        {messages.length > 1 && (
                            <Button variant="ghost" size="sm" onClick={clearChat} className="text-zinc-400 hover:text-red-400">
                                <Trash2 className="h-4 w-4 mr-1" />
                                Temizle
                            </Button>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col p-0">
                    {/* Chat Area */}
                    <div className="flex-1 p-4 space-y-4 overflow-y-auto max-h-[600px]">
                        {messages.map((m, i) => (
                            <div key={i} className={`flex w-full ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`flex max-w-[80%] rounded-lg px-4 py-2 text-sm ${m.role === 'user'
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-muted text-muted-foreground'
                                    }`}>
                                    {m.role !== 'user' && (
                                        <div className="mr-2 mt-0.5 shrink-0 flex flex-col items-center">
                                            <Bot className="h-4 w-4" />
                                            {/* Show model info on message if available/tracked? For now simple*/}
                                        </div>
                                    )}
                                    {m.role === 'user' && <User className="h-4 w-4 mr-2 mt-0.5 shrink-0" />}
                                    <div className="whitespace-pre-wrap">{m.content}</div>
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex w-full justify-start">
                                <div className="flex max-w-[80%] rounded-lg px-4 py-2 text-sm bg-muted text-muted-foreground animate-pulse">
                                    <Bot className="h-4 w-4 mr-2" /> Typing...
                                </div>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 border-t flex gap-2">
                        <Input
                            placeholder="Ask about VRAM requirements or market prices..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            disabled={loading}
                        />
                        <Button onClick={handleSend} disabled={loading} size="icon">
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
