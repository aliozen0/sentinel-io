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

                        <div className="mt-6 space-y-4">
                            <div className="p-3 rounded-md bg-yellow-500/10 border border-yellow-500/20 text-sm text-yellow-400">
                                <div className="flex items-start gap-2">
                                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-yellow-500" />
                                    <div className="space-y-1">
                                        <p className="font-medium text-yellow-500">Önemli Bilgilendirme</p>
                                        <p className="text-xs leading-relaxed opacity-90 text-yellow-200/80">
                                            Render.com altyapısı ("Cold Start") nedeniyle giriş işlemi 60 saniye kadar sürebilir. Lütfen sabırla bekleyiniz.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="p-3 rounded-md bg-zinc-950/50 border border-zinc-800 space-y-2">
                                <p className="text-xs font-medium text-zinc-400 text-center uppercase tracking-wider">Örnek Hesap Bilgileri</p>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="flex flex-col items-center p-2 rounded bg-zinc-900/50 border border-zinc-800/50">
                                        <span className="text-zinc-500 text-[10px] uppercase mb-1">Kullanıcı Adı</span>
                                        <span className="text-zinc-200 font-mono font-medium tracking-wide">admin</span>
                                    </div>
                                    <div className="flex flex-col items-center p-2 rounded bg-zinc-900/50 border border-zinc-800/50">
                                        <span className="text-zinc-500 text-[10px] uppercase mb-1">Şifre</span>
                                        <span className="text-zinc-200 font-mono font-medium tracking-wide">1234</span>
                                    </div>
                                </div>
                            </div>
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
