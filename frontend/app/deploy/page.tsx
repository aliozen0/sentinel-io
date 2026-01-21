"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Play, Radio, Loader2 } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = NEXT_PUBLIC_API_URL.replace("http", "ws")

import { SshConnectionModal } from "@/components/ssh-connection-modal"

export default function DeployPage() {
    const [mode, setMode] = useState<"simulation" | "live">("simulation")
    const [jobId, setJobId] = useState<string | null>(null)
    const [logs, setLogs] = useState<string[]>([])
    const [running, setRunning] = useState(false)
    const [showSshModal, setShowSshModal] = useState(false)
    const [showDemoModal, setShowDemoModal] = useState(false)
    const [demoCredentials, setDemoCredentials] = useState<any>(null)
    const [sshConfig, setSshConfig] = useState<any>(null)
    const logEndRef = useRef<HTMLDivElement>(null)

    const startDeployment = async () => {
        setLogs([])
        setRunning(true)
        try {
            const endpoint = mode === "simulation" ? "/v1/deploy/simulate" : "/v1/deploy/live"
            const res = await fetch(`${NEXT_PUBLIC_API_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_config: { image: "ray/project-ml" } })
            })

            if (res.ok) {
                const data = await res.json()
                setJobId(data.job_id)
                connectToLogs(data.job_id)
            }
        } catch (error) {
            console.error(error)
            setRunning(false)
        }
    }

    const connectToLogs = (id: string) => {
        const ws = new WebSocket(`${WS_URL}/ws/logs/${id}`)

        ws.onmessage = (event) => {
            setLogs(prev => [...prev, event.data])
        }

        ws.onclose = () => {
            setRunning(false)
            setLogs(prev => [...prev, "--- Connection Closed ---"])
        }
    }

    // Auto-scroll logs
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [logs])

    return (
        <div className="p-8 space-y-8 h-full flex flex-col">
            <h2 className="text-3xl font-bold tracking-tight">Deployment Console</h2>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
                {/* Config Panel */}
                <Card className="col-span-1 h-fit">
                    <CardHeader>
                        <CardTitle>Configuration</CardTitle>
                        <CardDescription>Select deployment mode.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="space-y-4">
                            <div
                                className={`p-4 border rounded-lg cursor-pointer transition ${mode === 'simulation' ? 'border-primary bg-primary/5' : 'hover:bg-muted'}`}
                                onClick={() => setMode("simulation")}
                            >
                                <div className="font-semibold flex items-center">
                                    <div className={`w-4 h-4 rounded-full border mr-3 ${mode === 'simulation' ? 'border-primary bg-primary' : 'border-muted-foreground'}`} />
                                    Simulation Mode 🤖
                                </div>
                                <p className="text-xs text-muted-foreground mt-2 pl-7">
                                    Test deployment on our mock GPU server. Get demo credentials below.
                                </p>
                                {mode === 'simulation' && (
                                    <div className="mt-3 ml-7 space-y-2">
                                        <p className="text-xs text-blue-400">
                                            👉 For testing: Check your terminal for demo SSH credentials or use your own test server below.
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div
                                className={`p-4 border rounded-lg cursor-pointer transition ${mode === 'live' ? 'border-primary bg-primary/5' : 'hover:bg-muted'}`}
                                onClick={() => setMode("live")}
                            >
                                <div className="font-semibold flex items-center">
                                    <div className={`w-4 h-4 rounded-full border mr-3 ${mode === 'live' ? 'border-primary bg-primary' : 'border-muted-foreground'}`} />
                                    Live Mode ⚡
                                </div>
                                <p className="text-xs text-muted-foreground mt-2 pl-7">
                                    Deploy to your real GPU server (or use demo below for testing).
                                </p>

                                {/* Demo Credentials Button */}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="ml-7 mt-3 w-[calc(100%-28px)] text-xs border-dashed border-blue-500 bg-blue-500/5 hover:bg-blue-500/10 text-blue-400 hover:text-blue-300"
                                    onClick={async (e) => {
                                        e.stopPropagation()
                                        try {
                                            const [demoRes, keyRes] = await Promise.all([
                                                fetch(`${NEXT_PUBLIC_API_URL}/v1/connections/demo`),
                                                fetch(`${NEXT_PUBLIC_API_URL}/v1/connections/demo/key`)
                                            ])

                                            if (demoRes.ok && keyRes.ok) {
                                                const demo = await demoRes.json()
                                                const keyData = await keyRes.json()

                                                setDemoCredentials({
                                                    hostname: demo.hostname,
                                                    port: demo.port,
                                                    username: demo.username,
                                                    privateKey: keyData.private_key,
                                                    description: demo.description
                                                })
                                                setShowDemoModal(true)
                                            } else {
                                                setLogs(prev => [...prev, '❌ Failed to fetch demo credentials'])
                                            }
                                        } catch (err) {
                                            setLogs(prev => [...prev, `❌ Demo error: ${err}`])
                                        }
                                    }}
                                >
                                    🎮 Get Demo Server Credentials
                                </Button>

                                {/* Connect Remote Server Button */}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="ml-7 mt-2 w-[calc(100%-28px)] text-xs border-dashed border-zinc-600 hover:border-emerald-500 hover:text-emerald-500"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        setShowSshModal(true)
                                    }}
                                >
                                    + Connect Remote Server
                                </Button>
                            </div>
                        </div>

                        <Button className="w-full" size="lg" onClick={startDeployment} disabled={running}>
                            {running ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                            {running ? "Deploying..." : "Initialise Deployment"}
                        </Button>
                    </CardContent>
                </Card>

                {/* Log Console */}
                <Card className="col-span-1 lg:col-span-2 flex flex-col bg-black text-green-500 font-mono border-zinc-800">
                    <CardHeader className="py-4 border-b border-zinc-800">
                        <CardTitle className="text-sm flex items-center text-zinc-400">
                            <Terminal className="w-4 h-4 mr-2" />
                            Live Logs: {jobId || "Waiting for job..."}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 overflow-y-auto p-4 min-h-[500px]">
                        {logs.length === 0 && !running && (
                            <div className="text-zinc-600 italic">Ready to accept log stream...</div>
                        )}
                        {logs.map((line, i) => (
                            <div key={i} className="whitespace-pre-wrap break-all">{line}</div>
                        ))}
                        <div ref={logEndRef} />
                    </CardContent>
                </Card>
            </div>

            <SshConnectionModal
                isOpen={showSshModal}
                onClose={() => setShowSshModal(false)}
                initialValues={sshConfig}
                onSave={(config: any) => {
                    setSshConfig(config)
                    setLogs(prev => [...prev, `✅ Connected to ${config.hostname}:${config.port}`])
                }}
            />

            {/* Demo Credentials Modal */}
            {showDemoModal && demoCredentials && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl p-6">
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="text-blue-500">🎮</span> Demo GPU Server Credentials
                        </h2>

                        <div className="space-y-4">
                            <div className="bg-blue-500/10 border border-blue-500/30 rounded p-3 text-sm text-blue-300">
                                <p className="mb-2">ℹ️ This is a real Docker container (mock-gpu-node)</p>
                                <p>{demoCredentials.description}</p>
                            </div>

                            <div className="space-y-2">
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                    <span className="text-zinc-400">Hostname:</span>
                                    <span className="col-span-2 font-mono text-white">{demoCredentials.hostname}</span>

                                    <span className="text-zinc-400">Port:</span>
                                    <span className="col-span-2 font-mono text-white">{demoCredentials.port}</span>

                                    <span className="text-zinc-400">Username:</span>
                                    <span className="col-span-2 font-mono text-white">{demoCredentials.username}</span>
                                </div>
                            </div>

                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded p-3 text-xs text-emerald-300">
                                ✨ Click "Auto-Fill Connection" below to automatically populate the SSH form!
                            </div>

                            <div className="flex gap-3 pt-4">
                                <Button
                                    variant="ghost"
                                    onClick={() => setShowDemoModal(false)}
                                    className="flex-1 text-zinc-400 hover:text-white"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    onClick={() => {
                                        // Auto-fill SSH connection modal with demo credentials
                                        setSshConfig({
                                            hostname: demoCredentials.hostname,
                                            port: demoCredentials.port,
                                            username: demoCredentials.username,
                                            privateKey: demoCredentials.privateKey
                                        })
                                        setShowDemoModal(false)
                                        setShowSshModal(true)
                                        setLogs(prev => [...prev,
                                            `📋 Demo credentials loaded!`,
                                            `   → Opening SSH connection modal...`,
                                        `   → Hostname: ${demoCredentials.hostname}:${demoCredentials.port}`,
                                        `   → Username: ${demoCredentials.username}`,
                                            `   → Private Key: ✅ Loaded`
                                        ])
                                    }}
                                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white"
                                >
                                    ✨ Auto-Fill Connection
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
