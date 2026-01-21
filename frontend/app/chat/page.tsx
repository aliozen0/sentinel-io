"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Send, Bot, User } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ChatPage() {
    const [messages, setMessages] = useState<{ role: string, content: string }[]>([
        { role: "assistant", content: "Hello! I am io-Guard Intelligence. How can I help you optimize your training today?" }
    ])
    const [input, setInput] = useState("")
    const [loading, setLoading] = useState(false)

    const handleSend = async () => {
        if (!input.trim()) return

        const userMsg = { role: "user", content: input }
        setMessages(prev => [...prev, userMsg])
        setInput("")
        setLoading(true)

        try {
            // Include history in a real app
            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages: [...messages, userMsg] })
            })

            if (res.ok) {
                const data = await res.json()
                setMessages(prev => [...prev, data]) // Expected: { role: "assistant", content: "..."}
            } else {
                setMessages(prev => [...prev, { role: "assistant", content: "Error: Could not reach the Brain." }])
            }
        } catch (error) {
            console.error(error)
            setMessages(prev => [...prev, { role: "assistant", content: "Error: Connection failure." }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="h-full p-8 flex flex-col space-y-4">
            <h2 className="text-3xl font-bold tracking-tight">io Intelligence</h2>

            <Card className="flex-1 flex flex-col min-h-[500px]">
                <CardHeader className="border-b">
                    <CardTitle className="flex items-center text-lg">
                        <Bot className="mr-2 h-5 w-5 text-purple-500" />
                        AI Agent
                        <span className="ml-2 text-xs text-muted-foreground font-normal bg-purple-500/10 px-2 py-1 rounded-full text-purple-500">
                            DeepSeek-V3
                        </span>
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
                                    {m.role !== 'user' && <Bot className="h-4 w-4 mr-2 mt-0.5 shrink-0" />}
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
