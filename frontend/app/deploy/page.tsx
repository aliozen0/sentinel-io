"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Loader2, Upload, FileCode, CheckCircle2, XCircle, Rocket, Server, KeyRound, Copy, ExternalLink } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = NEXT_PUBLIC_API_URL.replace("http", "ws")

import { SshConnectionModal } from "@/components/ssh-connection-modal"

export default function DeployPage() {
    const [jobId, setJobId] = useState<string | null>(null)
    const [logs, setLogs] = useState<string[]>([])
    const [running, setRunning] = useState(false)
    const [showSshModal, setShowSshModal] = useState(false)
    const [showDemoModal, setShowDemoModal] = useState(false)
    const [demoCredentials, setDemoCredentials] = useState<any>(null)
    const [sshConfig, setSshConfig] = useState<any>(null)
    const [connectionVerified, setConnectionVerified] = useState(false)
    const [loadingDemo, setLoadingDemo] = useState(false)
    const logEndRef = useRef<HTMLDivElement>(null)

    // Planned deployment state
    const [plannedConfig, setPlannedConfig] = useState<any>(null)

    // Check for Analyze params on mount
    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const gpu = params.get("gpu")

        if (gpu) {
            setPlannedConfig({
                gpu: gpu,
                price: params.get("price"),
                image: params.get("image"),
                setup: params.get("setup")
            })
            // Auto open SSH modal to encourage connection
            setShowSshModal(true)
        }
    }, [])

    // File upload state
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [uploadedFile, setUploadedFile] = useState<any>(null)
    const [uploading, setUploading] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Copy to clipboard helper
    const copyToClipboard = async (text: string, label: string) => {
        try {
            await navigator.clipboard.writeText(text)
            setLogs(prev => [...prev, `📋 ${label} copied to clipboard`])
        } catch (err) {
            console.error('Copy failed:', err)
        }
    }

    // Fetch demo credentials and show modal
    const fetchDemoCredentials = async () => {
        setLoadingDemo(true)
        setLogs(prev => [...prev, "🔄 Fetching demo server credentials..."])

        try {
            // First get connection info
            const demoRes = await fetch(`${NEXT_PUBLIC_API_URL}/v1/connections/demo`)

            if (!demoRes.ok) {
                throw new Error(`HTTP ${demoRes.status}`)
            }

            const demoData = await demoRes.json()

            if (!demoData.available) {
                setLogs(prev => [...prev, `⚠️ Demo server: ${demoData.message || 'Not available'}`])
                setLogs(prev => [...prev, `💡 Make sure Docker is running: docker-compose up --build`])
                setLoadingDemo(false)
                return
            }

            // Then get the private key
            const keyRes = await fetch(`${NEXT_PUBLIC_API_URL}/v1/connections/demo/key`)
            const keyData = await keyRes.json()

            if (!keyData.private_key) {
                setLogs(prev => [...prev, `❌ Demo key not ready: ${keyData.error || 'Please wait and try again'}`])
                setLoadingDemo(false)
                return
            }

            // Store credentials and show modal
            setDemoCredentials({
                hostname: demoData.hostname,
                port: demoData.port,
                username: demoData.username,
                privateKey: keyData.private_key,
                description: demoData.description,
                note: demoData.note
            })

            setShowDemoModal(true)
            setLogs(prev => [...prev, `✅ Demo credentials retrieved successfully!`])

        } catch (err: any) {
            console.error("Demo fetch error:", err)
            setLogs(prev => [...prev, `❌ Cannot connect to backend`])
            setLogs(prev => [...prev, `💡 Is Docker running? Try: docker-compose up --build`])
        } finally {
            setLoadingDemo(false)
        }
    }

    // Handle file selection
    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            if (!file.name.endsWith('.py')) {
                setLogs(prev => [...prev, "❌ Only Python (.py) files are allowed"])
                return
            }
            setSelectedFile(file)
            setUploadedFile(null)
            setLogs(prev => [...prev, `📁 Selected: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`])
        }
    }

    // Upload file to backend
    const handleUpload = async () => {
        if (!selectedFile) return

        setUploading(true)
        setLogs(prev => [...prev, `📤 Uploading ${selectedFile.name}...`])

        try {
            const formData = new FormData()
            formData.append('file', selectedFile)

            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/upload`, {
                method: 'POST',
                body: formData
            })

            if (res.ok) {
                const data = await res.json()
                setUploadedFile(data)
                setLogs(prev => [...prev,
                    `✅ Upload successful!`,
                `   📍 Server path: ${data.local_path}`,
                `   📊 Size: ${data.size} bytes`
                ])
            } else {
                const error = await res.json()
                setLogs(prev => [...prev, `❌ Upload failed: ${error.detail}`])
            }
        } catch (err) {
            setLogs(prev => [...prev, `❌ Upload error: ${err}`])
        } finally {
            setUploading(false)
        }
    }

    // Execute script on remote server
    const handleExecute = async () => {
        if (!uploadedFile || !sshConfig) {
            setLogs(prev => [...prev, "❌ Please upload a file and configure SSH connection first"])
            return
        }

        setRunning(true)
        setLogs(prev => [...prev, "", "═".repeat(50), "🚀 STARTING REMOTE EXECUTION", "═".repeat(50)])

        try {
            const body: any = {
                hostname: sshConfig.hostname,
                username: sshConfig.username,
                port: sshConfig.port || 22,
                auth_type: sshConfig.authType || "key",
                script_path: uploadedFile.local_path
            };

            // Add auth credentials based on type
            if (sshConfig.authType === "password") {
                body.password = sshConfig.password;
            } else {
                body.private_key = sshConfig.privateKey;
                if (sshConfig.passphrase) {
                    body.passphrase = sshConfig.passphrase;
                }
            }

            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/deploy/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            })

            if (res.ok) {
                const data = await res.json()
                setJobId(data.job_id)
                setLogs(prev => [...prev, `📋 Job ID: ${data.job_id}`])

                const ws = new WebSocket(`${WS_URL}/ws/execute/${data.job_id}`)

                ws.onmessage = (event) => {
                    setLogs(prev => [...prev, event.data])
                }

                ws.onclose = () => {
                    setRunning(false)
                    setLogs(prev => [...prev, "", "═".repeat(50), "📌 EXECUTION COMPLETED", "═".repeat(50)])
                }

                ws.onerror = () => {
                    setLogs(prev => [...prev, `❌ WebSocket connection error`])
                    setRunning(false)
                }
            } else {
                const error = await res.json()
                setLogs(prev => [...prev, `❌ Failed: ${error.detail}`])
                setRunning(false)
            }
        } catch (err) {
            setLogs(prev => [...prev, `❌ Execution error: ${err}`])
            setRunning(false)
        }
    }

    // Auto-scroll logs
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [logs])

    return (
        <div className="p-8 space-y-6 h-full flex flex-col">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Live Deployment</h2>
                    <p className="text-zinc-400 mt-1">Deploy your Python script to a remote GPU server</p>
                </div>
                {connectionVerified && (
                    <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-sm">
                        <CheckCircle2 className="w-4 h-4" />
                        Connected to {sshConfig?.hostname}
                    </div>
                )}
            </div>

            {plannedConfig && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 flex items-center justify-between animate-in fade-in slide-in-from-top-4">
                    <div className="flex items-center gap-4">
                        <div className="bg-blue-500/20 p-2 rounded-full">
                            <Rocket className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-200">Deployment Configured from Analysis</h3>
                            <p className="text-sm text-blue-300">
                                Target: <span className="font-bold text-white">{plannedConfig.gpu}</span> (${plannedConfig.price}/hr) •
                                Environment: <span className="font-mono text-xs bg-blue-500/20 px-1 py-0.5 rounded ml-1">{plannedConfig.image}</span>
                            </p>
                        </div>
                    </div>
                    <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setShowSshModal(true)}
                    >
                        Configure Connection
                    </Button>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
                {/* Config Panel */}
                <Card className="col-span-1 h-fit bg-zinc-900/50 border-zinc-800">
                    <CardHeader className="pb-4">
                        <CardTitle className="flex items-center gap-2 text-lg">
                            <Server className="w-5 h-5 text-emerald-400" />
                            Configuration
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">

                        {/* Step 1: Connection */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-sm font-semibold">
                                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${connectionVerified ? 'bg-emerald-500 text-white' : 'bg-zinc-700 text-zinc-300'}`}>1</div>
                                <span className={connectionVerified ? 'text-emerald-400' : 'text-zinc-200'}>Connect to Server</span>
                                {connectionVerified && <CheckCircle2 className="w-4 h-4 text-emerald-400 ml-auto" />}
                            </div>

                            <div className="pl-9 space-y-2">
                                {/* Demo Server Button */}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="w-full justify-start gap-2 border-blue-500/50 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 hover:text-blue-300"
                                    onClick={fetchDemoCredentials}
                                    disabled={loadingDemo}
                                >
                                    {loadingDemo ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <span>🎮</span>
                                    )}
                                    {loadingDemo ? "Loading..." : "Get Demo Server Credentials"}
                                </Button>

                                {/* Custom Server Button */}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className={`w-full justify-start gap-2 ${connectionVerified
                                        ? 'border-emerald-500/50 text-emerald-400'
                                        : 'border-zinc-700 hover:border-zinc-600 text-zinc-400'
                                        }`}
                                    onClick={() => setShowSshModal(true)}
                                >
                                    <KeyRound className="w-4 h-4" />
                                    {connectionVerified ? '✓ Change Connection' : '+ Add Remote Server'}
                                </Button>
                            </div>
                        </div>

                        {/* Step 2: File Upload */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-sm font-semibold">
                                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${uploadedFile ? 'bg-emerald-500 text-white' : 'bg-zinc-700 text-zinc-300'}`}>2</div>
                                <span className={uploadedFile ? 'text-emerald-400' : 'text-zinc-200'}>Upload Script</span>
                                {uploadedFile && <CheckCircle2 className="w-4 h-4 text-emerald-400 ml-auto" />}
                            </div>

                            <div className="pl-9 space-y-2">
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".py"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />

                                {!selectedFile ? (
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={!connectionVerified}
                                        className={`w-full p-4 border-2 border-dashed rounded-lg text-center transition-all ${connectionVerified
                                            ? 'border-zinc-600 hover:border-zinc-500 cursor-pointer group'
                                            : 'border-zinc-800 cursor-not-allowed opacity-50'
                                            }`}
                                    >
                                        <Upload className="w-8 h-8 mx-auto mb-2 text-zinc-500 group-hover:text-zinc-300" />
                                        <p className="text-sm text-zinc-400 group-hover:text-zinc-200">
                                            Select Python file
                                        </p>
                                    </button>
                                ) : (
                                    <div className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
                                        <div className="flex items-center gap-3">
                                            <FileCode className="w-8 h-8 text-blue-400 flex-shrink-0" />
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-zinc-200 truncate">{selectedFile.name}</p>
                                                <p className="text-xs text-zinc-500">{(selectedFile.size / 1024).toFixed(2)} KB</p>
                                            </div>
                                            {uploadedFile ? (
                                                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                                            ) : (
                                                <button onClick={() => { setSelectedFile(null); if (fileInputRef.current) fileInputRef.current.value = '' }} className="p-1 hover:bg-zinc-700 rounded">
                                                    <XCircle className="w-4 h-4 text-zinc-500" />
                                                </button>
                                            )}
                                        </div>
                                        {!uploadedFile && (
                                            <Button size="sm" className="w-full mt-3 bg-blue-600 hover:bg-blue-500" onClick={handleUpload} disabled={uploading}>
                                                {uploading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Uploading...</> : <><Upload className="w-4 h-4 mr-2" /> Upload</>}
                                            </Button>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Step 3: Execute */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-sm font-semibold">
                                <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold bg-zinc-700 text-zinc-300">3</div>
                                <span className="text-zinc-200">Execute</span>
                            </div>
                            <div className="pl-9">
                                <Button
                                    className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20 h-12"
                                    onClick={handleExecute}
                                    disabled={running || !connectionVerified || !uploadedFile}
                                >
                                    {running ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Executing...</> : <><Rocket className="w-5 h-5 mr-2" /> Execute on Server</>}
                                </Button>
                                {(!connectionVerified || !uploadedFile) && (
                                    <p className="text-xs text-zinc-500 mt-2 text-center">
                                        {!connectionVerified ? "↑ Connect to a server first" : "↑ Upload a script first"}
                                    </p>
                                )}
                            </div>
                        </div>

                    </CardContent>
                </Card>

                {/* Terminal */}
                <Card className="col-span-1 lg:col-span-2 flex flex-col bg-zinc-950 border-zinc-800">
                    <CardHeader className="py-3 border-b border-zinc-800 bg-zinc-900/50">
                        <CardTitle className="text-sm flex items-center justify-between text-zinc-400">
                            <div className="flex items-center gap-2">
                                <Terminal className="w-4 h-4" />
                                <span>Terminal</span>
                            </div>
                            <div className="flex items-center gap-3">
                                {running && <div className="flex items-center gap-2 text-emerald-400"><div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /><span className="text-xs">Running</span></div>}
                                {logs.length > 0 && <button onClick={() => setLogs([])} className="text-xs text-zinc-500 hover:text-zinc-300">Clear</button>}
                            </div>
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 overflow-y-auto p-4 min-h-[500px] font-mono text-sm">
                        {logs.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-zinc-600">
                                <div className="text-center">
                                    <Terminal className="w-12 h-12 mx-auto mb-3 opacity-30" />
                                    <p>Ready for deployment</p>
                                    <p className="text-xs mt-1">Click "Get Demo Server Credentials" to start</p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-0.5">
                                {logs.map((line, i) => (
                                    <div key={i} className={`whitespace-pre-wrap break-all leading-relaxed ${line.startsWith('❌') ? 'text-red-400' :
                                        line.startsWith('✅') ? 'text-emerald-400' :
                                            line.startsWith('⚠️') || line.startsWith('💡') ? 'text-yellow-400' :
                                                line.startsWith('🚀') || line.startsWith('═') || line.startsWith('📌') ? 'text-blue-400 font-bold' :
                                                    line.startsWith('📋') || line.startsWith('📁') || line.startsWith('📍') || line.startsWith('🔄') ? 'text-cyan-400' :
                                                        line.startsWith('   ') ? 'text-zinc-400 pl-2' : 'text-zinc-300'
                                        }`}>{line}</div>
                                ))}
                                <div ref={logEndRef} />
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* SSH Connection Modal */}
            <SshConnectionModal
                isOpen={showSshModal}
                onClose={() => setShowSshModal(false)}
                initialValues={sshConfig}
                onSave={(config: any) => {
                    setSshConfig(config)
                    setConnectionVerified(true)
                    setLogs(prev => [...prev, `✅ Connected to ${config.hostname}:${config.port} as ${config.username}`])
                }}
            />

            {/* Demo Credentials Modal */}
            {showDemoModal && demoCredentials && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="w-full max-w-xl bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl overflow-hidden">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 p-4">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                🎮 Demo GPU Server Credentials
                            </h2>
                            <p className="text-blue-100 text-sm mt-1">
                                This is a real SSH server running in Docker - same workflow as connecting to a real GPU!
                            </p>
                        </div>

                        <div className="p-5 space-y-4">
                            {/* Info Box */}
                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm text-blue-300">
                                <p>📋 <strong>Copy these credentials</strong> and paste them into the "Add Remote Server" form. This is exactly how you would connect to a real io.net GPU node!</p>
                            </div>

                            {/* Credentials Grid */}
                            <div className="space-y-3">
                                {/* Hostname */}
                                <div className="flex items-center gap-3 p-3 bg-zinc-800 rounded-lg group">
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 mb-1">Hostname</p>
                                        <p className="font-mono text-white">{demoCredentials.hostname}</p>
                                    </div>
                                    <button
                                        onClick={() => copyToClipboard(demoCredentials.hostname, 'Hostname')}
                                        className="p-2 hover:bg-zinc-700 rounded opacity-50 group-hover:opacity-100 transition-opacity"
                                    >
                                        <Copy className="w-4 h-4 text-zinc-400" />
                                    </button>
                                </div>

                                {/* Port */}
                                <div className="flex items-center gap-3 p-3 bg-zinc-800 rounded-lg group">
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 mb-1">Port</p>
                                        <p className="font-mono text-white">{demoCredentials.port}</p>
                                    </div>
                                    <button
                                        onClick={() => copyToClipboard(String(demoCredentials.port), 'Port')}
                                        className="p-2 hover:bg-zinc-700 rounded opacity-50 group-hover:opacity-100 transition-opacity"
                                    >
                                        <Copy className="w-4 h-4 text-zinc-400" />
                                    </button>
                                </div>

                                {/* Username */}
                                <div className="flex items-center gap-3 p-3 bg-zinc-800 rounded-lg group">
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 mb-1">Username</p>
                                        <p className="font-mono text-white">{demoCredentials.username}</p>
                                    </div>
                                    <button
                                        onClick={() => copyToClipboard(demoCredentials.username, 'Username')}
                                        className="p-2 hover:bg-zinc-700 rounded opacity-50 group-hover:opacity-100 transition-opacity"
                                    >
                                        <Copy className="w-4 h-4 text-zinc-400" />
                                    </button>
                                </div>

                                {/* Private Key */}
                                <div className="p-3 bg-zinc-800 rounded-lg group">
                                    <div className="flex items-center justify-between mb-2">
                                        <p className="text-xs text-zinc-500">Private Key (RSA)</p>
                                        <button
                                            onClick={() => copyToClipboard(demoCredentials.privateKey, 'Private Key')}
                                            className="flex items-center gap-1 px-2 py-1 text-xs bg-zinc-700 hover:bg-zinc-600 rounded text-zinc-300"
                                        >
                                            <Copy className="w-3 h-3" /> Copy Key
                                        </button>
                                    </div>
                                    <pre className="font-mono text-xs text-zinc-400 bg-zinc-950 p-2 rounded max-h-24 overflow-y-auto">
                                        {demoCredentials.privateKey.substring(0, 200)}...
                                    </pre>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-3 pt-2">
                                <Button
                                    variant="ghost"
                                    onClick={() => setShowDemoModal(false)}
                                    className="flex-1 text-zinc-400"
                                >
                                    Close
                                </Button>
                                <Button
                                    onClick={() => {
                                        // Pre-fill SSH modal with demo credentials
                                        setSshConfig({
                                            hostname: demoCredentials.hostname,
                                            port: demoCredentials.port,
                                            username: demoCredentials.username,
                                            privateKey: demoCredentials.privateKey
                                        })
                                        setShowDemoModal(false)
                                        setShowSshModal(true)
                                        setLogs(prev => [...prev,
                                            `📋 Demo credentials loaded into form`,
                                            `👉 Click "Test Connection" to verify, then "Save"`
                                        ])
                                    }}
                                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 gap-2"
                                >
                                    <ExternalLink className="w-4 h-4" />
                                    Fill Connection Form →
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
