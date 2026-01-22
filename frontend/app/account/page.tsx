"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { ShieldCheck, User, Server, CreditCard, Clock } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function AccountPage() {
    const router = useRouter()
    const [user, setUser] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const token = localStorage.getItem("token")
                if (!token) {
                    router.push("/login")
                    return
                }

                const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/auth/me`, {
                    headers: { "Authorization": `Bearer ${token}` }
                })

                if (res.ok) {
                    const data = await res.json()
                    setUser(data)
                } else if (res.status === 401) {
                    localStorage.removeItem("token")
                    router.push("/login")
                }
            } catch (err) {
                console.error("Failed to load user profile", err)
            } finally {
                setLoading(false)
            }
        }
        fetchUser()
    }, [router])

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
            </div>
        )
    }

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-400">
                    <User className="h-6 w-6" />
                </div>
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Account Settings</h2>
                    <p className="text-muted-foreground">Manage your profile and system preferences.</p>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Profile Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-emerald-500" />
                            User Profile
                        </CardTitle>
                        <CardDescription>Your identity within the io-Guard ecosystem.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-1">
                            <div className="text-sm font-medium text-zinc-500">Username</div>
                            <div className="text-lg font-mono">{user?.username || "Unknown"}</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-sm font-medium text-zinc-500">User ID</div>
                            <div className="text-xs font-mono bg-zinc-950 p-2 rounded text-zinc-400">
                                {user?.id}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* System Status Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Server className="h-5 w-5 text-blue-500" />
                            System Status
                        </CardTitle>
                        <CardDescription>Current operating mode and resource allocation.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <div className="text-sm font-medium text-zinc-500">Operating Mode</div>
                                <div className="font-bold flex items-center gap-2">
                                    {user?.mode === "CLOUD" ? (
                                        <span className="text-blue-400">CLOUD</span>
                                    ) : (
                                        <span className="text-amber-400">LOCAL</span>
                                    )}
                                    <span className="text-xs font-normal text-zinc-500 border border-zinc-700 px-2 py-0.5 rounded">
                                        {user?.mode === "CLOUD" ? "Supabase Connected" : "SQLite Database"}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2 pt-4 border-t border-zinc-800">
                            <div className="flex items-center justify-between text-sm">
                                <span className="flex items-center gap-2 text-zinc-400">
                                    <CreditCard className="h-4 w-4" />
                                    Available Credits
                                </span>
                                <span className="font-mono text-emerald-500">${user?.credits?.toFixed(2)}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                                <span className="flex items-center gap-2 text-zinc-400">
                                    <Clock className="h-4 w-4" />
                                    Session Valid Until
                                </span>
                                <span className="font-mono text-zinc-500">24 Hours</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
