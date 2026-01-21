"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Play, Radio, Loader2 } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = NEXT_PUBLIC_API_URL.replace("http", "ws")

export default function DeployPage() {
    const [mode, setMode] = useState<"simulation" | "live">("simulation")
    const [jobId, setJobId] = useState<string | null>(null)
    const [logs, setLogs] = useState<string[]>([])
    const [running, setRunning] = useState(false)
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
                                    Simulation Mode
                                </div>
                                <p className="text-xs text-muted-foreground mt-2 pl-7">
                                    Dry-run the training on a virtual node. No credits deducted.
                                </p>
                            </div>

                            <div
                                className={`p-4 border rounded-lg cursor-pointer transition ${mode === 'live' ? 'border-primary bg-primary/5' : 'hover:bg-muted'}`}
                                onClick={() => setMode("live")}
                            >
                                <div className="font-semibold flex items-center">
                                    <div className={`w-4 h-4 rounded-full border mr-3 ${mode === 'live' ? 'border-primary bg-primary' : 'border-muted-foreground'}`} />
                                    Live Deployment
                                </div>
                                <p className="text-xs text-muted-foreground mt-2 pl-7">
                                    Provision real GPU hardware on io.net. Credits will be used.
                                </p>
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
        </div>
    )
}
