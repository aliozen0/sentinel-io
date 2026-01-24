"use client"

import { useState, useRef, DragEvent, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { CheckCircle2, AlertTriangle, XCircle, Search, Cpu, Package, Terminal, Zap, Upload, FileCode, Clock, Brain, Server, Activity, RotateCcw } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const ANALYZE_STORAGE_KEY = "io-guard-analyze-session"

// Pipeline Step Component
function PipelineStep({ step, isActive }: { step: any, isActive: boolean }) {
    const icons: Record<string, any> = {
        "Auditor": Brain,
        "Architect": Package,
        "Sniper": Cpu
    }
    const Icon = icons[step.agent] || Activity

    const colors: Record<string, string> = {
        "Auditor": "text-yellow-500 border-yellow-500/30 bg-yellow-500/10",
        "Architect": "text-purple-500 border-purple-500/30 bg-purple-500/10",
        "Sniper": "text-emerald-500 border-emerald-500/30 bg-emerald-500/10"
    }

    return (
        <div className={`p-3 rounded-lg border transition-all ${step.status === "completed"
            ? colors[step.agent] || "border-zinc-700"
            : isActive
                ? "border-blue-500 bg-blue-500/10 animate-pulse"
                : "border-zinc-800 bg-zinc-900/50"
            }`}>
            <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step.status === "completed" ? "bg-current/20" : "bg-zinc-800"
                    }`}>
                    <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">{step.agent}</span>
                        {step.status === "completed" && (
                            <span className="text-xs text-zinc-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {step.duration_sec}s
                            </span>
                        )}
                    </div>
                    <p className="text-xs text-zinc-500 truncate">{step.action}</p>
                </div>
                {step.status === "completed" && (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                )}
            </div>

            {/* Step Details */}
            {step.details && (
                <div className="mt-2 pl-11 space-y-1">
                    {Object.entries(step.details).map(([key, value]) => (
                        <div key={key} className="text-xs flex gap-2">
                            <span className="text-zinc-600">{key}:</span>
                            <span className="text-zinc-400 font-mono truncate">{String(value)}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Step Result */}
            {step.result && (
                <div className="mt-2 pl-11 flex flex-wrap gap-2">
                    {Object.entries(step.result).map(([key, value]) => (
                        <span key={key} className="px-2 py-0.5 bg-zinc-800 rounded text-xs">
                            <span className="text-zinc-500">{key}:</span>{" "}
                            <span className="text-white font-medium">{String(value)}</span>
                        </span>
                    ))}
                </div>
            )}
        </div>
    )
}

export default function AnalyzePage() {
    const [code, setCode] = useState("")
    const [fileName, setFileName] = useState<string | null>(null)
    const [fileInfo, setFileInfo] = useState<any>(null) // New state for file metadata
    const [budget, setBudget] = useState(10.0)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)
    const [isDragging, setIsDragging] = useState(false)
    const [showResetConfirm, setShowResetConfirm] = useState(false) // State for confirmation modal
    const [jobId, setJobId] = useState<string | null>(null)
    const [pipelineTrace, setPipelineTrace] = useState<any[]>([])
    const resultRef = useRef<HTMLDivElement>(null) // Ref for scrolling
    const [showPipeline, setShowPipeline] = useState(true)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Model selection state
    const [models, setModels] = useState<any[]>([])
    const [selectedModel, setSelectedModel] = useState<string>("")
    const [loadingModels, setLoadingModels] = useState(true)

    // Load from sessionStorage on mount
    useEffect(() => {
        try {
            const stored = sessionStorage.getItem(ANALYZE_STORAGE_KEY)
            if (stored) {
                const parsed = JSON.parse(stored)
                if (parsed.code) setCode(parsed.code)
                if (parsed.fileName) setFileName(parsed.fileName)
                if (parsed.fileInfo) setFileInfo(parsed.fileInfo)
                if (parsed.budget) setBudget(parsed.budget)
                if (parsed.result) {
                    setResult(parsed.result)
                    // Restore trace from result if available
                    if (parsed.result.pipeline_trace?.steps) {
                        setPipelineTrace(parsed.result.pipeline_trace.steps)
                    }
                }
                if (parsed.selectedModel) setSelectedModel(parsed.selectedModel)
                if (parsed.jobId) setJobId(parsed.jobId)
            }
        } catch (e) {
            console.error("Failed to load analyze session:", e)
        }
    }, [])

    // Save to sessionStorage on state changes
    useEffect(() => {
        if (code || result) {
            try {
                sessionStorage.setItem(ANALYZE_STORAGE_KEY, JSON.stringify({
                    code, fileName, fileInfo, budget, result, selectedModel, jobId
                }))
            } catch (e) {
                console.error("Failed to save analyze session:", e)
            }
        }
    }, [code, fileName, budget, result, selectedModel, jobId, fileInfo])

    // Fetch active session from server (Persistence)
    useEffect(() => {
        const fetchHistory = async () => {
            try {
                // strict check: if we verify we have a jobId in local storage, we skip overwriting
                // unless we want to sync status. 
                // BUT, if this is a new tab (jobId is null), we definitely want to check server.
                const token = localStorage.getItem("token")
                if (!token) return

                const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/analyze/history`, {
                    headers: { "Authorization": `Bearer ${token}` }
                })

                if (res.ok) {
                    const data = await res.json()
                    // Find active job (RUNNING or PENDING)
                    const activeJob = data.jobs?.find((j: any) =>
                        ["PENDING", "RUNNING"].includes(j.status)
                    )

                    if (activeJob) {
                        console.log("Found active job from server:", activeJob.id)

                        // If we are blank or different, sync
                        if (!jobId || jobId !== activeJob.id) {
                            setJobId(activeJob.id)

                            // Restore metadata if available
                            if (activeJob.metadata) {
                                if (activeJob.metadata.code) setCode(activeJob.metadata.code)
                                if (activeJob.metadata.input_budget) setBudget(activeJob.metadata.input_budget)
                                if (activeJob.metadata.model) setSelectedModel(activeJob.metadata.model)
                                if (activeJob.metadata.pipeline_trace) setPipelineTrace(activeJob.metadata.pipeline_trace)
                            }
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to fetch history:", e)
            }
        }

        // Short delay to let session storage load first, then check server
        setTimeout(fetchHistory, 500)
    }, [])


    // Fetch models on mount
    useEffect(() => {
        fetch(`${NEXT_PUBLIC_API_URL}/v1/models`)
            .then(res => res.json())
            .then(data => {
                setModels(data.models)
                // Only set default if not restored from session
                if (!selectedModel) setSelectedModel(data.default_model)
                setLoadingModels(false)
            })
            .catch(err => {
                console.error("Failed to fetch models:", err)
                setLoadingModels(false)
            })
    }, [])

    // Handle file upload (Single or Project)
    const handleFileUpload = async (files: FileList) => {
        if (!files || files.length === 0) return
        setLoading(true) // Show loading on textarea if needed or just use uploading state
        setCode("# Yükleniyor...")
        setResult(null)

        try {
            const formData = new FormData()
            // Check if multiple files or ZIP
            const isProject = files.length > 1 || files[0].name.endsWith('.zip')

            const token = localStorage.getItem("token")
            const headers: any = {}
            if (token) headers["Authorization"] = `Bearer ${token}`

            // Add files to FormData
            if (isProject) {
                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i])
                }
            } else {
                formData.append('file', files[0])
            }

            // Decide Endpoint
            const endpoint = isProject ? '/v1/upload/project' : '/v1/upload'

            const res = await fetch(`${NEXT_PUBLIC_API_URL}${endpoint}`, {
                method: 'POST',
                headers: headers,
                body: formData
            })

            const data = await res.json()

            if (!res.ok) {
                throw new Error(data.detail || "Upload failed")
            }

            // Handle Response
            if (isProject) {
                const info = {
                    ...data,
                    isProject: true,
                    filename: `${data.file_count || files.length} files (${files[0].name.endsWith('.zip') ? 'ZIP' : 'Folder'})`
                }
                setFileName(info.filename)

                // Fetch Code Content for Project
                // Helper to fetch text from project dir
                const fetchProjectFile = async (path: string) => {
                    try {
                        const res = await fetch(`${NEXT_PUBLIC_API_URL}/uploads/project_${data.project_id}/${path}`)
                        if (res.ok) return await res.text()
                    } catch (e) { console.error(e) }
                    return null
                }

                let combinedCode = ""
                // 1. Entry Point
                if (data.entry_point) {
                    const entryContent = await fetchProjectFile(data.entry_point)
                    if (entryContent) combinedCode += `# === ENTRY POINT: ${data.entry_point} ===\n${entryContent}\n\n`
                }

                // 2. Fetch other important files
                if (data.files) {
                    const otherFiles = data.files.filter((f: any) =>
                        f.filename !== data.entry_point &&
                        (f.filename.endsWith('.py') || f.filename.endsWith('.yaml') || f.filename === 'requirements.txt')
                    )

                    for (const f of otherFiles.slice(0, 5)) {
                        const content = await fetchProjectFile(f.filename)
                        if (content) combinedCode += `# === FILE: ${f.filename} ===\n${content}\n\n`
                    }
                    if (otherFiles.length > 5) combinedCode += `# ... and ${otherFiles.length - 5} more files ...`
                }

                setCode(combinedCode)

            } else {
                // Single File
                setFileName(data.original_name)
                // Fetch content from URL or just read locally (we already have the file)
                const reader = new FileReader()
                reader.onload = (e) => setCode(e.target?.result as string)
                reader.readAsText(files[0])
            }

        } catch (err: any) {
            console.error(err)
            alert(`Yükleme hatası: ${err.message}`)
            setCode("")
            setFileName(null)
        } finally {
            setLoading(false)
        }
    }

    // Drag & Drop handlers
    const handleDragOver = (e: DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e: DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleDrop = (e: DragEvent) => {
        e.preventDefault()
        setIsDragging(false)

        const files = e.dataTransfer.files
        if (files.length > 0) {
            handleFileUpload(files)
        }
    }

    const handleFileClick = () => {
        fileInputRef.current?.click()
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files
        if (files && files.length > 0) {
            handleFileUpload(files)
        }
    }

    const handleClearFile = () => {
        setCode("")
        setFileName(null)
        setFileInfo(null)
        setResult(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ""
        }
    }

    const handleReset = () => {
        setShowResetConfirm(true)
    }

    const executeReset = () => {
        handleClearFile()
        setBudget(10.0)
        setJobId(null)
        setPipelineTrace([])
        sessionStorage.removeItem(ANALYZE_STORAGE_KEY)
        setShowResetConfirm(false)
    }

    const handleAnalyze = async () => {
        if (!code.trim()) {
            alert('Please upload or paste code first')
            return
        }

        setLoading(true)
        setResult(null)
        setPipelineTrace([])

        try {
            const token = localStorage.getItem("token")
            if (!token) {
                window.location.href = "/login"
                return
            }

            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/analyze`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    code,
                    budget,
                    model: selectedModel
                })
            })
            if (res.ok) {
                const data = await res.json()
                setJobId(data.job_id)
                // Don't set result yet, wait for WebSocket updates
            } else {
                const err = await res.json()
                alert(err.detail || "Analysis failed")
                setLoading(false)
            }
        } catch (error) {
            console.error(error)
            setLoading(false)
        }
    }

    const handleLoadDemo = async () => {
        try {
            const res = await fetch('/examples/demo_script.py')
            if (res.ok) {
                const text = await res.text()
                setCode(text)
                setFileName("demo_script.py")
            } else {
                alert("Demo file not found")
            }
        } catch (e) {
            console.error(e)
            alert("Failed to load demo")
        }
    }

    // WebSocket for Analysis Job
    useEffect(() => {
        if (!jobId) return

        setLoading(true)
        const wsUrl = NEXT_PUBLIC_API_URL.replace('http', 'ws')
        const ws = new WebSocket(`${wsUrl}/ws/analyze/${jobId}`)

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)

                if (data.pipeline_trace) {
                    setPipelineTrace(data.pipeline_trace)
                }

                if (data.status === "COMPLETED" && data.result) {
                    setResult(data.result)
                    setLoading(false)
                    setJobId(null) // Job done, stop tracking
                    setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
                } else if (data.status === "FAILED") {
                    setLoading(false)
                    setJobId(null)
                    alert("Analysis Failed via Background Job")
                }
            } catch (e) {
                console.error("WS Parse Error", e)
            }
        }

        ws.onclose = () => {
            // If connection closes but job not done? 
            // We might want to reconnect or just leave it.
            // For now, if closed by server (job done), we are fine.
        }

        return () => {
            ws.close()
        }
    }, [jobId])

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-emerald-500"
        if (score >= 50) return "text-yellow-500"
        return "text-red-500"
    }

    return (
        <div className="p-8 space-y-6 h-full flex flex-col">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Code Audit & Planning</h2>
                    <p className="text-zinc-400 mt-1">Upload your training script, get GPU recommendations</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={handleReset} size="sm" className="border-zinc-700 hover:bg-zinc-800 text-zinc-300">
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Sıfırla
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
                {/* Input Column */}
                <div className="flex flex-col gap-4">
                    <Card className="flex-1 flex flex-col bg-zinc-900/50 border-zinc-800 min-h-0">
                        <CardHeader className="pb-2">
                            <CardTitle className="flex items-center gap-2 text-base">
                                <Terminal className="w-4 h-4 text-blue-400" />
                                Source Code
                                {fileName ? (
                                    <span className="ml-auto text-sm font-normal text-zinc-400 flex items-center gap-2">
                                        <FileCode className="w-4 h-4" />
                                        {fileName}
                                        <button
                                            onClick={handleClearFile}
                                            className="text-zinc-500 hover:text-red-400 ml-1"
                                        >
                                            ✕
                                        </button>
                                    </span>
                                ) : (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleLoadDemo}
                                        className="ml-auto text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 h-7"
                                    >
                                        <FileCode className="w-3 h-3 mr-1" />
                                        Load Demo
                                    </Button>
                                )}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 flex flex-col space-y-3 min-h-0">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                                accept=".py,.zip"
                                multiple
                                className="hidden"
                            />

                            {!code ? (
                                <div
                                    onDragOver={handleDragOver}
                                    onDragLeave={handleDragLeave}
                                    onDrop={handleDrop}
                                    onClick={handleFileClick}
                                    className={`flex-1 min-h-[300px] border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all ${isDragging
                                        ? 'border-blue-500 bg-blue-500/10'
                                        : 'border-zinc-700 hover:border-zinc-500 bg-zinc-950'
                                        }`}
                                >
                                    <Upload className={`w-10 h-10 mb-3 ${isDragging ? 'text-blue-400' : 'text-zinc-500'}`} />
                                    <p className={`font-medium ${isDragging ? 'text-blue-400' : 'text-zinc-400'}`}>
                                        {isDragging ? 'Drop your file here' : 'Drop Python file here'}
                                    </p>
                                    <p className="text-xs text-zinc-600 mt-1">or click to browse</p>
                                </div>
                            ) : (
                                <div
                                    className="relative flex-1 min-h-0"
                                    onDragOver={handleDragOver}
                                    onDragLeave={handleDragLeave}
                                    onDrop={handleDrop}
                                >
                                    {loading && (
                                        <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center text-blue-400">
                                            <Activity className="w-12 h-12 animate-spin mb-4" />
                                            <p className="font-semibold text-lg animate-pulse">Analiz Ediliyor...</p>
                                            <p className="text-sm text-blue-300 mt-2">Bu işlem 10-30 saniye sürebilir.</p>
                                        </div>
                                    )}
                                    <Textarea
                                        className="font-mono text-xs h-full min-h-[300px] bg-zinc-950 border-zinc-800 resize-none p-4"
                                        value={code}
                                        onChange={(e) => setCode(e.target.value)}
                                        disabled={loading}
                                    />
                                </div>
                            )}

                            <div className="flex items-center gap-3">
                                <div className="flex-[2]">
                                    <span className="text-xs text-zinc-400 mb-1 block">AI Model</span>
                                    <select
                                        className="w-full h-9 bg-zinc-950 border border-zinc-800 rounded-md px-3 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        value={selectedModel}
                                        onChange={(e) => setSelectedModel(e.target.value)}
                                        disabled={loadingModels}
                                    >
                                        {models.map(m => (
                                            <option key={m.id} value={m.id}>
                                                {m.name} {m.recommended ? "(Recommended)" : ""}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="flex-1">
                                    <span className="text-xs text-zinc-400 mb-1 block">Budget ($/hr)</span>
                                    <Input
                                        type="number"
                                        value={budget}
                                        onChange={(e) => setBudget(parseFloat(e.target.value))}
                                        className="bg-zinc-950 border-zinc-800 h-9"
                                    />
                                </div>
                                <Button
                                    className="mt-5 bg-blue-600 hover:bg-blue-500 h-9"
                                    onClick={handleAnalyze}
                                    disabled={loading || !code.trim()}
                                >
                                    {loading ? "Analyzing..." : "Run Audit"}
                                    <Search className="ml-2 h-4 w-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Pipeline Trace */}
                    {(loading || pipelineTrace.length > 0) && (
                        <Card className="bg-zinc-900/50 border-zinc-800">
                            <CardHeader className="pb-2">
                                <CardTitle className="flex items-center gap-2 text-base">
                                    <Activity className="w-4 h-4 text-blue-400" />
                                    Pipeline Trace
                                    {result?.pipeline_trace && (
                                        <span className="ml-auto text-xs font-normal text-zinc-500 flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            Total: {result.pipeline_trace.total_duration_sec}s
                                        </span>
                                    )}
                                </CardTitle>
                                <CardDescription className="text-xs">
                                    See exactly what's happening behind the scenes
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {pipelineTrace.length > 0 ? (
                                    <div className="space-y-2">
                                        {pipelineTrace.map((step, idx) => (
                                            <PipelineStep
                                                key={step.step || idx}
                                                step={step}
                                                isActive={step.status === 'running'}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-zinc-500 text-xs p-4 text-center animate-pulse">
                                        Starting analysis agents...
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Output Column */}
                <div className="space-y-4 overflow-y-auto">
                    {result ? (
                        <div ref={resultRef} className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">

                            {/* Summary Card */}
                            {result.summary && (
                                <Card className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border-blue-500/30">
                                    <CardContent className="py-3">
                                        <div className="grid grid-cols-5 gap-3 text-center">
                                            <div>
                                                <div className="text-[10px] text-zinc-400 uppercase">Framework</div>
                                                <div className="font-bold text-sm text-blue-400">{result.summary.framework}</div>
                                            </div>
                                            <div>
                                                <div className="text-[10px] text-zinc-400 uppercase">VRAM</div>
                                                <div className="font-bold text-sm text-purple-400">{result.summary.vram_required}</div>
                                            </div>
                                            <div>
                                                <div className="text-[10px] text-zinc-400 uppercase">GPU</div>
                                                <div className="font-bold text-sm text-emerald-400">{result.summary.recommended_gpu}</div>
                                            </div>
                                            <div>
                                                <div className="text-[10px] text-zinc-400 uppercase">Setup</div>
                                                <div className="font-bold text-sm text-yellow-400">{result.summary.estimated_setup}</div>
                                            </div>
                                            <div>
                                                <div className="text-[10px] text-zinc-400 uppercase">Health</div>
                                                <div className={`font-bold text-sm ${getScoreColor(result.summary.health_score)}`}>
                                                    {result.summary.health_score}/100
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Auditor Report */}
                            <Card className="bg-zinc-900/50 border-zinc-800">
                                <CardHeader className="pb-2">
                                    <CardTitle className="flex items-center text-sm">
                                        <Zap className="w-4 h-4 mr-2 text-yellow-500" />
                                        Auditor Report
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    {result.audit.critical_issues?.length > 0 && (
                                        <div className="bg-red-500/10 p-2 rounded-md border border-red-500/20">
                                            <h4 className="text-red-400 font-semibold mb-1 flex items-center text-xs">
                                                <XCircle className="h-3 w-3 mr-1" /> Issues ({result.audit.critical_issues.length})
                                            </h4>
                                            <ul className="list-disc list-inside text-xs space-y-0.5 text-red-300">
                                                {result.audit.critical_issues.map((issue: string, i: number) => (
                                                    <li key={i}>{issue}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {result.audit.suggestions?.length > 0 && (
                                        <div className="bg-blue-500/10 p-2 rounded-md border border-blue-500/20">
                                            <h4 className="text-blue-400 font-semibold mb-1 text-xs">💡 Suggestions</h4>
                                            <ul className="list-disc list-inside text-xs space-y-0.5 text-blue-300">
                                                {result.audit.suggestions.map((s: string, i: number) => (
                                                    <li key={i}>{s}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Environment Plan - Compact */}
                            <Card className="bg-zinc-900/50 border-zinc-800">
                                <CardHeader className="pb-2">
                                    <CardTitle className="flex items-center text-sm">
                                        <Package className="w-4 h-4 mr-2 text-purple-500" />
                                        Environment
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    <div className="font-mono text-xs bg-zinc-950 p-2 rounded border border-zinc-800">
                                        <span className="text-purple-400">FROM</span>{" "}
                                        <span className="text-emerald-400">{result.environment.base_image}</span>
                                    </div>

                                    {result.environment.python_packages?.length > 0 && (
                                        <div className="flex flex-wrap gap-1">
                                            {result.environment.python_packages.map((pkg: string, i: number) => (
                                                <span key={i} className="px-1.5 py-0.5 bg-blue-500/20 text-blue-300 rounded text-[10px] font-mono">
                                                    {pkg}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    <div className="grid grid-cols-3 gap-1">
                                        <div className="text-center p-1.5 bg-zinc-800/50 rounded">
                                            <div className="text-[10px] text-zinc-500">CUDA</div>
                                            <div className="font-bold text-xs">{result.environment.cuda_version || "N/A"}</div>
                                        </div>
                                        <div className="text-center p-1.5 bg-zinc-800/50 rounded">
                                            <div className="text-[10px] text-zinc-500">GPU</div>
                                            <div className="font-bold text-xs">{result.environment.gpu_required ? "Required" : "Optional"}</div>
                                        </div>
                                        <div className="text-center p-1.5 bg-zinc-800/50 rounded">
                                            <div className="text-[10px] text-zinc-500">Setup</div>
                                            <div className="font-bold text-xs">{result.environment.estimated_setup_time_min}m</div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* GPU Recommendations */}
                            <Card className="bg-zinc-900/50 border-zinc-800">
                                <CardHeader className="pb-2">
                                    <CardTitle className="flex items-center text-sm">
                                        <Cpu className="w-4 h-4 mr-2 text-emerald-500" />
                                        GPU Options
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-1.5">
                                        {result.market_recommendations?.map((node: any, i: number) => (
                                            <div
                                                key={i}
                                                className={`flex items-center justify-between p-2 border rounded-lg ${i === 0
                                                    ? 'border-emerald-500/50 bg-emerald-500/5'
                                                    : 'border-zinc-800'
                                                    }`}
                                            >
                                                <div className="flex items-center gap-2">
                                                    {i === 0 && <span className="text-[10px] bg-emerald-500 text-white px-1.5 py-0.5 rounded">BEST</span>}
                                                    <div>
                                                        <div className="font-bold text-xs">{node.gpu_model}</div>
                                                        <div className="text-[10px] text-zinc-500">
                                                            {node.idle_nodes}/{node.total_nodes} avail • {node.reliability}%
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <div className="text-right">
                                                        <div className="text-emerald-400 font-bold text-sm">${node.price_hourly}/hr</div>
                                                        <div className="text-[10px] text-zinc-500">Score: {node.score?.toFixed(2)}</div>
                                                    </div>
                                                    <Button
                                                        size="sm"
                                                        className="h-7 text-xs bg-zinc-800 hover:bg-blue-600 hover:text-white border border-zinc-700 transition-colors"
                                                        onClick={() => {
                                                            const params = new URLSearchParams({
                                                                gpu: node.gpu_model,
                                                                price: node.price_hourly.toString(),
                                                                image: result.environment.base_image,
                                                                setup: result.environment.setup_commands.join(' && ')
                                                            })
                                                            window.location.href = `/deploy?${params.toString()}`
                                                        }}
                                                    >
                                                        Deploy
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    ) : (
                        <div className="h-full flex items-center justify-center text-zinc-500 border-2 border-dashed border-zinc-800 rounded-lg">
                            <div className="text-center">
                                <Search className="w-10 h-10 mx-auto mb-2 opacity-30" />
                                <p className="text-sm">Upload code to analyze</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Confirmation Modal */}
            {showResetConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <Card className="w-full max-w-md bg-zinc-900 border-zinc-800 shadow-xl scale-100 animate-in zoom-in-95 duration-200">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-red-400">
                                <AlertTriangle className="w-5 h-5" />
                                Sıfırlama Onayı
                            </CardTitle>
                            <CardDescription>
                                Mevcut analizi, yüklenen dosyaları ve tüm ayarları temizlemek üzeresiniz. Bu işlem geri alınamaz.
                            </CardDescription>
                        </CardHeader>
                        <div className="p-6 pt-0 flex justify-end gap-3">
                            <Button
                                variant="outline"
                                onClick={() => setShowResetConfirm(false)}
                                className="border-zinc-700 hover:bg-zinc-800 text-zinc-300"
                            >
                                İptal
                            </Button>
                            <Button
                                variant="destructive"
                                onClick={executeReset}
                                className="bg-red-600 hover:bg-red-700"
                            >
                                Evet, Sıfırla
                            </Button>
                        </div>
                    </Card>
                </div>
            )}
        </div>
    )
}
