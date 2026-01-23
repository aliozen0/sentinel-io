"use client"

import { useState, useEffect, useRef } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Send, Bot, User, Trash2, Cpu, Sparkles, Terminal, Copy, Check } from "lucide-react"
import {
    getChatMessages,
    saveChatMessages,
    completePendingRequest,
    hasPendingRequest,
    sendChatMessage,
    ChatMessage
} from "@/lib/chat-service"

const CHAT_STORAGE_KEY = "io-guard-chat-messages"

// --- Helper Components ---

const MessageBubble = ({ message }: { message: ChatMessage }) => {
    const isUser = message.role === 'user'

    // Simple code block parser
    const renderContent = (content: string) => {
        const parts = content.split(/(```[\s\S]*?```)/g)
        return parts.map((part, index) => {
            if (part.startsWith('```') && part.endsWith('```')) {
                const codeContent = part.slice(3, -3).replace(/^[a-z]+\n/, '') // remove lang if possible
                return (
                    <div key={index} className="my-3 overflow-hidden rounded-md bg-black/80 border border-white/10 shadow-sm">
                        <div className="flex items-center justify-between px-3 py-1.5 bg-white/5 border-b border-white/5">
                            <div className="flex items-center gap-2">
                                <Terminal className="w-3 h-3 text-emerald-400" />
                                <span className="text-xs text-zinc-400 font-mono">Code Block</span>
                            </div>
                        </div>
                        <pre className="p-3 overflow-x-auto text-xs sm:text-sm font-mono text-zinc-300">
                            <code>{codeContent.trim()}</code>
                        </pre>
                    </div>
                )
            }

            // Format text parts (currently just bold)
            const textParts = part.split(/(\*\*.*?\*\*)/g)
            return (
                <span key={index} className="whitespace-pre-wrap leading-relaxed">
                    {textParts.map((subPart, subIndex) => {
                        if (subPart.startsWith('**') && subPart.endsWith('**')) {
                            return <strong key={subIndex} className="font-bold text-zinc-100">{subPart.slice(2, -2)}</strong>
                        }
                        return subPart
                    })}
                </span>
            )
        })
    }

    return (
        <div className={`flex w-full mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[90%] md:max-w-[80%] gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>

                {/* Avatar */}
                <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-lg border ${isUser
                    ? 'bg-blue-600/20 border-blue-500/30 text-blue-400'
                    : 'bg-purple-600/20 border-purple-500/30 text-purple-400'
                    }`}>
                    {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                </div>

                {/* Message Content */}
                <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                    <div className={`px-5 py-3.5 rounded-2xl text-sm shadow-md backdrop-blur-sm border ${isUser
                        ? 'bg-blue-600 text-white rounded-tr-sm border-blue-500/0'
                        : 'bg-zinc-900/60 text-zinc-100 rounded-tl-sm border-white/10'
                        }`}>
                        {renderContent(message.content)}
                    </div>
                    {/* Timestamp or Status could go here */}
                </div>
            </div>
        </div>
    )
}

export default function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [input, setInput] = useState("")
    const [loading, setLoading] = useState(false)
    const chatEndRef = useRef<HTMLDivElement>(null)

    // Model Selection State
    const [models, setModels] = useState<any[]>([])
    const [selectedModel, setSelectedModel] = useState<string>("")
    const [loadingModels, setLoadingModels] = useState(true)

    // Load messages and check for pending requests on mount
    useEffect(() => {
        const loadedMessages = getChatMessages()
        // If empty, show welcome message
        if (loadedMessages.length === 0) {
            setMessages([{ role: "assistant", content: "Merhaba! Ben io-Guard Asistanı.\nSize sistem durumu, optimizasyon veya geliştirme konularında nasıl yardımcı olabilirim?" }])
        } else {
            setMessages(loadedMessages)
        }

        if (hasPendingRequest()) {
            setLoading(true)
            completePendingRequest().then((response) => {
                if (response) {
                    setMessages(getChatMessages())
                }
                setLoading(false)
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
                if (!selectedModel) setSelectedModel(data.default_model)
                setLoadingModels(false)
            })
            .catch(err => {
                console.error("Failed to fetch models:", err)
                setLoadingModels(false)
            })
    }, [])

    // Save messages on change
    useEffect(() => {
        if (messages.length > 0) {
            saveChatMessages(messages)
        }
    }, [messages])

    // Scroll to bottom
    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, loading])

    const clearChat = () => {
        sessionStorage.removeItem(CHAT_STORAGE_KEY)
        setMessages([{ role: "assistant", content: "Sohbet geçmişi temizlendi. Yeni bir başlangıç yapalım!" }])
    }

    const handleSend = async () => {
        if (!input.trim()) return

        const userMsg: ChatMessage = { role: "user", content: input }
        const updatedMessages = [...messages, userMsg]
        setMessages(updatedMessages)
        setInput("")
        setLoading(true)

        try {
            await sendChatMessage(
                messages,
                userMsg,
                (response) => {
                    setMessages(prev => [...prev, response])
                    setLoading(false)
                },
                (error) => {
                    setMessages(prev => [...prev, { role: "assistant", content: `Bir hata oluştu: ${error}` }])
                    setLoading(false)
                },
                selectedModel
            )
        } catch (error) {
            console.error(error)
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-y-0 right-0 left-0 md:left-72 flex flex-col bg-black/20 overflow-hidden z-10">
            {/* --- Header --- */}
            <div className="flex-none h-16 border-b border-white/5 bg-black/20 backdrop-blur-md flex items-center justify-between px-6 z-10">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-500 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                        <Bot className="text-white w-5 h-5" />
                    </div>
                    <div>
                        <h1 className="font-semibold text-zinc-100 leading-tight">io Intelligence</h1>
                        <div className="flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-xs text-zinc-400">Online & Ready</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Model Selector Pill */}
                    <div className="hidden md:flex items-center bg-white/5 rounded-full px-3 py-1 border border-white/5 hover:bg-white/10 transition-colors">
                        <Cpu className="w-3.5 h-3.5 text-zinc-400 mr-2" />
                        <select
                            className="bg-transparent text-xs text-zinc-300 focus:outline-none cursor-pointer [&>option]:bg-zinc-900"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            disabled={loadingModels || loading}
                        >
                            {models.length > 0 ? (
                                models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)
                            ) : (
                                <option>Loading...</option>
                            )}
                        </select>
                    </div>

                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={clearChat}
                        className="text-zinc-400 hover:text-red-400 hover:bg-red-400/10 rounded-full h-9 w-9"
                        title="Temizle"
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* --- Chat Area --- */}
            <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent p-4 md:p-8">
                <div className="max-w-4xl mx-auto flex flex-col justify-end min-h-full pb-4">
                    {/* Welcome / Empty State Placeholder if needed, handled by initial message */}

                    {messages.map((m, i) => (
                        <MessageBubble key={i} message={m} />
                    ))}

                    {/* Loading Indicator */}
                    {loading && (
                        <div className="flex w-full mb-6 justify-start">
                            <div className="flex max-w-[80%] gap-3 flex-row">
                                <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-purple-600/20 border border-purple-500/30 text-purple-400">
                                    <Sparkles className="w-4 h-4 animate-pulse" />
                                </div>
                                <div className="px-5 py-3.5 rounded-2xl rounded-tl-sm bg-zinc-900/60 border border-white/10 text-zinc-400 text-sm flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>
            </div>

            {/* --- Input Area --- */}
            <div className="flex-none p-4 md:p-6 bg-gradient-to-t from-black/80 to-transparent">
                <div className="max-w-3xl mx-auto relative group">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-full blur opacity-50 group-hover:opacity-100 transition duration-500" />
                    <div className="relative flex items-center bg-zinc-900/90 backdrop-blur-xl border border-white/10 rounded-full shadow-2xl px-2 py-2">
                        <Input
                            className="flex-1 border-none bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 px-4 py-3 placeholder:text-zinc-500 text-base"
                            placeholder="Bir şeyler sorun... (Örn: Modelimi nasıl optimize ederim?)"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            disabled={loading}
                        />
                        <Button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            size="icon"
                            className={`h-10 w-10 rounded-full transition-all duration-300 ${input.trim() ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/30' : 'bg-transparent text-zinc-600 hover:bg-zinc-800'
                                }`}
                        >
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                    <div className="absolute -bottom-6 left-0 right-0 text-center">
                        <p className="text-[10px] text-zinc-600">
                            AI modelleri hata yapabilir. Önemli bilgileri kontrol ediniz.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
