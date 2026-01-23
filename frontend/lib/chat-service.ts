// Chat Service - Handles API requests in the background
// This ensures chat responses are received even when navigating away

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const CHAT_STORAGE_KEY = "io-guard-chat-messages"
const CHAT_PENDING_KEY = "io-guard-chat-pending"

export interface ChatMessage {
    role: string
    content: string
    sources?: { title: string, url: string, score: number }[]
}

interface PendingRequest {
    id: string
    messages: ChatMessage[]
    model?: string
    timestamp: number
}

// Get stored messages
export function getChatMessages(): ChatMessage[] {
    try {
        const stored = sessionStorage.getItem(CHAT_STORAGE_KEY)
        if (stored) {
            return JSON.parse(stored)
        }
    } catch (e) {
        console.error("Failed to load chat:", e)
    }
    return [{ role: "assistant", content: "Hello! I am io-Guard Intelligence. How can I help you?" }]
}

// Save messages
export function saveChatMessages(messages: ChatMessage[]): void {
    try {
        sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages))
    } catch (e) {
        console.error("Failed to save chat:", e)
    }
}

// Check for pending request and complete it
export async function completePendingRequest(): Promise<ChatMessage | null> {
    try {
        const pendingStr = sessionStorage.getItem(CHAT_PENDING_KEY)
        if (!pendingStr) return null

        const pending: PendingRequest = JSON.parse(pendingStr)

        // If request is older than 60 seconds, discard it
        if (Date.now() - pending.timestamp > 60000) {
            sessionStorage.removeItem(CHAT_PENDING_KEY)
            return null
        }

        // Complete the request
        const token = typeof window !== 'undefined' ? localStorage.getItem("token") : null
        const headers: Record<string, string> = { "Content-Type": "application/json" }
        if (token) headers["Authorization"] = `Bearer ${token}`

        const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/chat`, {
            method: "POST",
            headers,
            body: JSON.stringify({
                messages: pending.messages,
                model: pending.model
            })
        })

        sessionStorage.removeItem(CHAT_PENDING_KEY)

        if (res.ok) {
            const data = await res.json()

            // Add response to stored messages
            const messages = getChatMessages()
            messages.push(data)
            saveChatMessages(messages)

            return data
        }
    } catch (e) {
        console.error("Failed to complete pending request:", e)
        sessionStorage.removeItem(CHAT_PENDING_KEY)
    }
    return null
}

// Send message with background handling
export async function sendChatMessage(
    messages: ChatMessage[],
    userMessage: ChatMessage,
    onResponse: (msg: ChatMessage) => void,
    onError: (error: string) => void,
    model?: string
): Promise<void> {
    const allMessages = [...messages, userMessage]

    // Save pending request in case user navigates away
    const pending: PendingRequest = {
        id: Date.now().toString(),
        messages: allMessages,
        model: model,
        timestamp: Date.now()
    }
    sessionStorage.setItem(CHAT_PENDING_KEY, JSON.stringify(pending))

    try {
        const token = typeof window !== 'undefined' ? localStorage.getItem("token") : null
        const headers: Record<string, string> = { "Content-Type": "application/json" }
        if (token) headers["Authorization"] = `Bearer ${token}`

        const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/chat`, {
            method: "POST",
            headers,
            body: JSON.stringify({
                messages: allMessages,
                model: model
            })
        })

        // Clear pending since we got response
        sessionStorage.removeItem(CHAT_PENDING_KEY)

        if (res.ok) {
            const data = await res.json()
            onResponse(data)
        } else {
            onError("Could not reach the AI")
        }
    } catch (error) {
        // Don't clear pending on network error - might recover later
        onError("Connection failure")
    }
}

// Check if there's a pending request
export function hasPendingRequest(): boolean {
    return sessionStorage.getItem(CHAT_PENDING_KEY) !== null
}
