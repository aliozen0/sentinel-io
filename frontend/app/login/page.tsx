"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Lock, Server, AlertCircle } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function LoginPage() {
    const router = useRouter()
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError("")

        try {
            // Backend expects OAuth2 form data
            const formData = new URLSearchParams()
            formData.append("username", username)
            formData.append("password", password)

            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData,
            })

            const data = await res.json()

            if (!res.ok) {
                // Handle Cloud Mode Error specifically
                if (res.status === 400 && data.detail?.includes("Cloud Mode")) {
                    throw new Error("System is in Cloud Mode. Please use Supabase Login.")
                }
                throw new Error(data.detail || "Login failed")
            }

            // Success
            localStorage.setItem("token", data.access_token)
            router.push("/")

        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-zinc-950 p-4">
            <Card className="w-full max-w-md border-zinc-800 bg-zinc-900/50">
                <CardHeader className="text-center space-y-2">
                    <div className="mx-auto h-12 w-12 rounded-full bg-emerald-500/10 flex items-center justify-center mb-2">
                        <Lock className="h-6 w-6 text-emerald-500" />
                    </div>
                    <CardTitle className="text-2xl font-bold">Welcome Back</CardTitle>
                    <CardDescription>
                        Sign in to io-Guard Mission Control
                    </CardDescription>
                </CardHeader>

                <form onSubmit={handleLogin}>
                    <CardContent className="space-y-4">
                        {error && (
                            <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-sm text-red-400">
                                <AlertCircle className="h-4 w-4" />
                                {error}
                            </div>
                        )}

                        <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400">
                            <p className="font-semibold mb-1">Example Account:</p>
                            <div className="grid grid-cols-2 gap-2 text-xs opacity-90">
                                <span>Username: <code className="bg-black/20 px-1 rounded">admin</code></span>
                                <span>Password: <code className="bg-black/20 px-1 rounded">1234</code></span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="username">Username</Label>
                            <Input
                                id="username"
                                placeholder="admin"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                className="bg-zinc-950/50 border-zinc-800 focus:border-emerald-500/50"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="bg-zinc-950/50 border-zinc-800 focus:border-emerald-500/50"
                            />
                        </div>

                        <div className="flex items-center gap-2 text-xs text-zinc-500 mt-4 justify-center">
                            <Server className="h-3 w-3" />
                            <span>System Mode: Auto-Detect (Local/Cloud)</span>
                        </div>
                    </CardContent>

                    <CardFooter>
                        <Button
                            type="submit"
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                            disabled={loading}
                        >
                            {loading ? "Authenticating..." : "Sign In"}
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    )
}
