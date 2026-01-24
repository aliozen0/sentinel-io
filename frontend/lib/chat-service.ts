import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
    id?: string
    createdAt?: Date
    sources?: any[]
}

const STORAGE_KEY = 'io-guard-chat-messages'
const PENDING_KEY = 'chat_pending_request'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const getChatMessages = (): ChatMessage[] => {
    if (typeof window === 'undefined') return []
    try {
        const stored = localStorage.getItem(STORAGE_KEY)
        return stored ? JSON.parse(stored) : []
    } catch (e) {
        console.error("Failed to load chat messages", e)
        return []
    }
}

export const saveChatMessages = (messages: ChatMessage[]) => {
    if (typeof window === 'undefined') return
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    } catch (e) {
        console.error("Failed to save chat messages", e)
    }
}

export const hasPendingRequest = (): boolean => {
    if (typeof window === 'undefined') return false
    return !!localStorage.getItem(PENDING_KEY)
}

export const completePendingRequest = async (): Promise<boolean> => {
    if (typeof window === 'undefined') return false
    localStorage.removeItem(PENDING_KEY)
    return true
}

export const sendChatMessage = async (
    history: ChatMessage[],
    newMessage: ChatMessage,
    onSuccess: (response: ChatMessage) => void,
    onError: (error: string) => void,
    model?: string
) => {
    try {
        const messages = [...history, newMessage].map(m => ({
            role: m.role,
            content: m.content
        }))

        const res = await fetch(`${API_URL}/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Add Authorization header if needed, assuming cookie-based or handled elsewhere
            },
            body: JSON.stringify({
                messages: messages,
                model: model
            })
        })

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || `Server error: ${res.status}`)
        }

        const data = await res.json()
        onSuccess(data)

    } catch (error: any) {
        console.error("Chat error:", error)
        onError(error.message || "Failed to send message")
    }
}
