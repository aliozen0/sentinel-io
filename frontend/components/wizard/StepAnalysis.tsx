"use client"

import { useState, useRef, DragEvent, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Search, Terminal, Upload, FileCode, Activity, ArrowRight, Brain, Package, Cpu, Clock, CheckCircle2, Info, ChevronDown, ChevronUp, AlertCircle, Loader2 } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Pipeline Component
function PipelineStep({ step, isActive }: { step: any, isActive: boolean }) {
    const icons: Record<string, any> = { "Auditor": Brain, "Architect": Package, "Sniper": Cpu }
    const Icon = icons[step.agent] || Activity
    const colors: Record<string, string> = {
        "Auditor": "text-yellow-500 border-yellow-500/30 bg-yellow-500/10",
        "Architect": "text-purple-500 border-purple-500/30 bg-purple-500/10",
        "Sniper": "text-emerald-500 border-emerald-500/30 bg-emerald-500/10"
    }

    return (
        <div className={`p-3 rounded-lg border transition-all ${step.status === "completed" ? colors[step.agent] || "border-zinc-700" : isActive ? "border-blue-500 bg-blue-500/10 animate-pulse" : "border-zinc-800 bg-zinc-900/50"}`}>
            <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step.status === "completed" ? "bg-current/20" : "bg-zinc-800"}`}>
                    <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">{step.agent}</span>
                        {step.status === "completed" && (
                            <span className="text-xs text-zinc-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" />{step.duration_sec}s
                            </span>
                        )}
                    </div>
                    <p className="text-xs text-zinc-500 truncate">{step.action}</p>
                </div>
                {step.status === "completed" && <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />}
            </div>
        </div>
    )
}

interface StepAnalysisProps {
    onComplete: (code: string, result: any, fileInfoData?: any) => void
    initialCode?: string
    initialResult?: any
    initialFileInfo?: any
}

export default function StepAnalysis({ onComplete, initialCode = "", initialResult = null, initialFileInfo = null }: StepAnalysisProps) {
    const [code, setCode] = useState(initialCode)
    const [fileName, setFileName] = useState<string | null>(initialFileInfo?.filename || null)
    const [fileInfo, setFileInfo] = useState<any>(initialFileInfo)
    const [budget, setBudget] = useState(10.0)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(initialResult)
    const [isDragging, setIsDragging] = useState(false)
    const [uploading, setUploading] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Expanded sections
    const [showWhatHappens, setShowWhatHappens] = useState(false)
    const [showFileDetails, setShowFileDetails] = useState(initialFileInfo ? true : false)
    const [showAuditDetails, setShowAuditDetails] = useState(false)
    const [showEnvDetails, setShowEnvDetails] = useState(false)

    // Model state
    const [models, setModels] = useState<any[]>([])
    const [selectedModel, setSelectedModel] = useState<string>("")
    const [loadingModels, setLoadingModels] = useState(true)

    // File stats
    const [fileStats, setFileStats] = useState<{ lines: number, size: number, chars: number } | null>(null)

    useEffect(() => {
        fetch(`${NEXT_PUBLIC_API_URL}/v1/models`)
            .then(res => res.json())
            .then(data => {
                setModels(data.models)
                setSelectedModel(data.default_model)
                setLoadingModels(false)
            })
            .catch(err => console.error("Failed to fetch models", err))
    }, [])

    // Initialize stats if fileInfo is present
    useEffect(() => {
        if (fileInfo) {
            setFileName(fileInfo.filename)
            if (initialCode) {
                const lines = initialCode.split('\n').length
                const size = new Blob([initialCode]).size
                setFileStats({ lines, size, chars: initialCode.length })
                setShowFileDetails(true)
            }
        }
    }, [])

    // Calculate file stats when code changes
    useEffect(() => {
        if (code) {
            const lines = code.split('\n').length
            const chars = code.length
            const size = new Blob([code]).size
            setFileStats({ lines, size, chars })
        } else if (!fileInfo) {
            setFileStats(null)
        }
    }, [code, fileInfo])

    // Recovery for lost state
    useEffect(() => {
        if (initialCode && initialCode.includes("# Proje Yüklendi") && !initialFileInfo) {
            setCode("")
            setFileName(null)
            // Optional: Notify user toast
        }
    }, [])

    const handleFileUpload = async (files: FileList) => {
        if (!files || files.length === 0) return
        setUploading(true)
        setResult(null)

        try {
            const formData = new FormData()
            const isProject = files.length > 1 || files[0].name.endsWith('.zip')

            const token = localStorage.getItem("token")
            const headers: any = {}
            if (token) headers["Authorization"] = `Bearer ${token}`

            // Upload Logic
            if (isProject) {
                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i])
                }

                const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/upload/project`, {
                    method: 'POST',
                    headers: headers,
                    body: formData
                })

                const data = await res.json()
                if (res.ok) {
                    const info = {
                        ...data,
                        isProject: true,
                        filename: `${data.file_count} dosya (${files[0].name.endsWith('.zip') ? 'ZIP' : 'Klasör'})`,
                        local_path: data.project_dir
                    }
                    setFileInfo(info)
                    setFileName(info.filename)

                    // Helper to fetch text from project dir
                    const fetchProjectFile = async (path: string) => {
                        try {
                            const res = await fetch(`${NEXT_PUBLIC_API_URL}/uploads/project_${data.project_id}/${path}`)
                            if (res.ok) return await res.text()
                        } catch (e) { console.error(e) }
                        return null
                    }

                    try {
                        let combinedCode = ""

                        // 1. Entry Point
                        const entryContent = await fetchProjectFile(data.entry_point)
                        if (entryContent) {
                            combinedCode += `# === ENTRY POINT: ${data.entry_point} ===\n${entryContent}\n\n`
                        } else {
                            combinedCode += `# Hata: Entry point (${data.entry_point}) okunamadı.\n\n`
                        }

                        // 2. Identify other important files (py, yaml, txt)
                        const otherFiles = data.files.filter((f: any) =>
                            f.filename !== data.entry_point &&
                            (f.filename.endsWith('.py') || f.filename.endsWith('.yaml') || f.filename.endsWith('.yml') || f.filename === 'requirements.txt')
                        )

                        // 3. Fetch top 5 other files
                        for (const f of otherFiles.slice(0, 5)) {
                            const content = await fetchProjectFile(f.filename)
                            if (content) {
                                combinedCode += `# === FILE: ${f.filename} ===\n${content}\n\n`
                            }
                        }

                        if (otherFiles.length > 5) {
                            combinedCode += `# ... ve diğer ${otherFiles.length - 5} dosya daha ...`
                        }

                        setCode(combinedCode)

                    } catch (e) {
                        console.error("Failed to fetch project files", e)
                        setCode(`# Hata: Dosyalar okunurken bir sorun oluştu.`)
                    }

                } else {
                    alert(`Yükleme hatası: ${data.detail || 'Bilinmeyen hata'}`)
                }

            } else {
                // Single File
                const file = files[0]
                if (!file.name.endsWith('.py')) {
                    alert('Lütfen bir Python dosyası veya ZIP projesi seçin.')
                    setUploading(false)
                    return
                }

                // Read locally for immediate feedback
                const reader = new FileReader()
                reader.onload = async (e) => {
                    const content = e.target?.result as string
                    setCode(content)
                    setFileName(file.name)
                }
                reader.readAsText(file)

                // Also upload to get consistent fileInfo structure
                formData.append('file', file)
                const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/upload`, {
                    method: 'POST',
                    headers: headers, // Reusing headers from above
                    body: formData
                })
                if (res.ok) {
                    const data = await res.json()
                    setFileInfo(data)
                }
            }

        } catch (err: any) {
            console.error(err)
            alert(`Yükleme başarısız: ${err.message}`)
        } finally {
            setUploading(false)
        }
    }

    const handleDragOver = (e: DragEvent) => { e.preventDefault(); setIsDragging(true) }
    const handleDragLeave = (e: DragEvent) => { e.preventDefault(); setIsDragging(false) }
    const handleDrop = (e: DragEvent) => {
        e.preventDefault(); setIsDragging(false)
        if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files)
    }

    const [jobId, setJobId] = useState<string | null>(null)
    const [pipelineTrace, setPipelineTrace] = useState<any[]>([])

    // WebSocket Effect
    useEffect(() => {
        if (!jobId) return

        // Construct WS URL (handle http/https -> ws/wss)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsBase = NEXT_PUBLIC_API_URL.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')
        const wsUrl = `${wsBase}/ws/analyze/${jobId}`

        console.log("Connecting to WS:", wsUrl)

        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
            console.log("WS Connected")
        }

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                // console.log("WS Message:", data)

                if (data.error) {
                    console.error("WS Error:", data.error)
                    // You might want to handle this UI wise
                    return
                }

                // Update result state with new data
                // Backend sends: { status, pipeline_trace, result } where result is the final report

                if (data.pipeline_trace) {
                    // Update trace state directly
                    const traceData = Array.isArray(data.pipeline_trace) ? data.pipeline_trace : (data.pipeline_trace.steps || [])
                    setPipelineTrace(traceData)
                }

                setResult((prev: any) => {
                    const newResult = {
                        ...prev,
                        status: data.status,
                        // Keep result if present (final report)
                        ...(data.result || {})
                    }
                    return newResult
                })

                if (data.status === "COMPLETED") {
                    setLoading(false)
                    ws.close()
                    setJobId(null)

                    // Force complete all steps
                    setPipelineTrace(prev => prev.map(s => ({ ...s, status: 'completed' })))
                } else if (data.status === "FAILED") {
                    setLoading(false)
                    ws.close()
                    setJobId(null)
                    alert("Analiz başarısız oldu. Lütfen tekrar deneyin.")
                }

            } catch (e) {
                console.error("WS Message Error:", e)
            }
        }

        ws.onerror = (e) => {
            console.error("WS Error:", e)
            // Don't stop loading immediately, maybe it reconnects or just temporary
        }

        ws.onclose = () => {
            console.log("WS Closed")
        }

        return () => {
            ws.close()
        }
    }, [jobId])

    const handleAnalyze = async () => {
        if (!code.trim()) return
        setLoading(true)
        setResult(null)
        setJobId(null)
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
                body: JSON.stringify({ code, budget, model: selectedModel })
            })
            if (res.ok) {
                const data = await res.json()
                // data = { job_id: "...", status: "PENDING" }
                // Start WS connection
                if (data.job_id) {
                    setJobId(data.job_id)
                    // The WS will handle result updates
                    // Initial result state
                    setResult({
                        pipeline_trace: { steps: [] },
                        status: "PENDING"
                    })
                    setShowAuditDetails(true)
                    setShowEnvDetails(true)
                } else {
                    // Fallback check if it returned result immediately (unlikely in v1)
                    setResult(data)
                    setLoading(false)
                }
            } else {
                setLoading(false)
                alert("Analiz başlatılamadı.")
            }
        } catch (error) {
            console.error(error)
            setLoading(false)
        }
    }

    return (
        <div className="h-full flex flex-col p-6 space-y-4">
            {/* Info Banner */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <h3 className="font-semibold text-blue-200 mb-1">Adım 1: Kod Analizi</h3>
                        <p className="text-sm text-blue-300/90">
                            Python projenizi veya script'inizi yükleyin. Sistem otomatik olarak gereksinimleri analiz edecek.
                            ZIP veya çoklu dosya yükleyebilirsiniz.
                        </p>
                        <button
                            onClick={() => setShowWhatHappens(!showWhatHappens)}
                            className="mt-2 text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                        >
                            {showWhatHappens ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            {showWhatHappens ? "Detayları Gizle" : "Ne Olacak? Detayları Gör"}
                        </button>
                        {showWhatHappens && (
                            <div className="mt-3 p-3 bg-blue-950/30 rounded border border-blue-500/20 text-xs space-y-2 text-blue-200">
                                <p><strong>1. Auditor Agent:</strong> Kodunuzu tarar, framework tespit eder, potansiyel sorunları bulur</p>
                                <p><strong>2. Architect Agent:</strong> Gerekli Python paketlerini, CUDA versiyonunu ve Docker image'ını belirler</p>
                                <p><strong>3. Sniper Agent:</strong> Bütçenize ve gereksinimlerinize uygun GPU'ları io.net marketinden bulur</p>
                                <p className="text-yellow-300">⏱️ Bu işlem yaklaşık 10-30 saniye sürer (AI modeline göre)</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
                {/* Left: Input & Pipeline */}
                <div className="flex flex-col gap-4 h-full">
                    {/* Code Input Card */}
                    <Card className="flex-1 flex flex-col bg-zinc-900/50 border-zinc-800">
                        <CardHeader className="pb-2">
                            <CardTitle className="flex items-center gap-2 text-base">
                                <Terminal className="w-4 h-4 text-blue-400" />
                                Kaynak Kod
                                {fileName && <span className="ml-auto text-sm font-normal text-zinc-400 truncate max-w-[200px]">{fileName}</span>}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 flex flex-col space-y-3 min-h-0">
                            <input type="file" ref={fileInputRef} onChange={(e) => e.target.files && handleFileUpload(e.target.files)} accept=".py,.zip" multiple className="hidden" />

                            {!code && !fileInfo ? (
                                <div
                                    onDragOver={handleDragOver}
                                    onDragLeave={handleDragLeave}
                                    onDrop={handleDrop}
                                    onClick={() => fileInputRef.current?.click()}
                                    className={`flex-1 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all ${isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-zinc-700 hover:border-zinc-500 bg-zinc-950'}`}
                                >
                                    {uploading ? (
                                        <div className="text-center">
                                            <Loader2 className="w-10 h-10 mb-3 text-blue-500 animate-spin mx-auto" />
                                            <p className="text-blue-400 font-medium">Yükleniyor...</p>
                                        </div>
                                    ) : (
                                        <>
                                            <Upload className="w-10 h-10 mb-3 text-zinc-500" />
                                            <p className="text-zinc-400 font-medium">Proje veya Script Sürükleyin</p>
                                            <p className="text-xs text-zinc-600 mt-1">.py, .zip veya klasör</p>
                                        </>
                                    )}
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col gap-2 min-h-0">
                                    {/* File Details Toggle ... (Keeping same) */}
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => setShowFileDetails(!showFileDetails)}
                                            className="flex-1 flex items-center justify-between p-2 bg-zinc-800/50 rounded text-xs hover:bg-zinc-800 transition"
                                        >
                                            <span className="text-zinc-400">📄 Dosya Detayları</span>
                                            {showFileDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                        </button>
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-8 w-8"
                                            onClick={() => {
                                                setCode("")
                                                setFileInfo(null)
                                                setFileName(null)
                                                setResult(null)
                                            }}
                                            title="Dosyayı Temizle"
                                        >
                                            <FileCode className="w-4 h-4" />
                                        </Button>
                                    </div>

                                    {showFileDetails && fileStats && (
                                        <div className="grid grid-cols-3 gap-2 p-2 bg-zinc-900/80 rounded text-xs">
                                            <div className="text-center">
                                                <div className="text-zinc-500">Satır </div>
                                                <div className="text-white font-bold">{fileStats.lines}</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-zinc-500">Karakter</div>
                                                <div className="text-white font-bold">{fileStats.chars}</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-zinc-500">Boyut</div>
                                                <div className="text-white font-bold">{(fileStats.size / 1024).toFixed(1)} KB</div>
                                            </div>
                                        </div>
                                    )}
                                    <Textarea
                                        className="flex-1 font-mono text-xs bg-zinc-950 border-zinc-800 resize-none min-h-[200px]"
                                        value={code}
                                        onChange={(e) => setCode(e.target.value)}
                                        placeholder="# Kodunuzu buraya yapıştırın veya dosya yükleyin..."
                                    />
                                </div>
                            )}

                            <div className="space-y-2 border-t border-zinc-800 pt-3">
                                <div className="flex gap-3 items-end">
                                    <div className="flex-1">
                                        <label className="text-xs text-zinc-400 mb-1 block">AI Model</label>
                                        <select
                                            className="w-full h-9 bg-zinc-950 border border-zinc-800 rounded-md px-3 text-sm"
                                            value={selectedModel}
                                            onChange={(e) => setSelectedModel(e.target.value)}
                                            disabled={loadingModels}
                                        >
                                            {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                                        </select>
                                    </div>
                                    <div className="w-28">
                                        <label className="text-xs text-zinc-400 mb-1 block">Bütçe ($/saat)</label>
                                        <Input type="number" step="0.1" value={budget} onChange={(e) => setBudget(parseFloat(e.target.value))} className="bg-zinc-950 border-zinc-800 h-9" />
                                    </div>
                                </div>
                                <Button
                                    className="w-full bg-blue-600 hover:bg-blue-500 h-10"
                                    onClick={handleAnalyze}
                                    disabled={loading || !code.trim()}
                                >
                                    {loading ? (
                                        <>
                                            <Activity className="w-4 h-4 mr-2 animate-spin" />
                                            Analiz Ediliyor...
                                        </>
                                    ) : (
                                        <>
                                            <Search className="w-4 h-4 mr-2" />
                                            Analizi Başlat
                                        </>
                                    )}
                                </Button>
                                {!code.trim() && (
                                    <p className="text-xs text-zinc-500 text-center">↑ Önce kod yükleyin</p>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Pipeline (Moved to Left Column, below code) */}
                    {(loading || pipelineTrace.length > 0) && (
                        <Card className="bg-zinc-900/50 border-zinc-800 animate-in fade-in slide-in-from-top-2">
                            <CardHeader className="pb-2">
                                <CardTitle className="flex items-center gap-2 text-sm">
                                    <Activity className="w-4 h-4 text-blue-400" />
                                    Analiz Pipeline
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {pipelineTrace.length === 0 ? (
                                    <>
                                        <PipelineStep step={{ agent: "Auditor", status: "running", action: "Kod analiz ediliyor..." }} isActive={true} />
                                        <PipelineStep step={{ agent: "Architect", status: "pending", action: "Bekliyor..." }} isActive={false} />
                                        <PipelineStep step={{ agent: "Sniper", status: "pending", action: "Bekliyor..." }} isActive={false} />
                                    </>
                                ) : (
                                    pipelineTrace.map((step: any, i: number) => (
                                        <PipelineStep key={i} step={step} isActive={step.status === 'running'} />
                                    ))
                                )}
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Right: Results (Only show when COMPLETED) */}
                <div className="flex flex-col gap-4 h-full overflow-y-auto">
                    {!loading && result?.status === "COMPLETED" ? (
                        <>
                            {/* Stats Dashboard */}
                            {result?.audit && (
                                <div className="grid grid-cols-5 gap-2 mb-4 animate-in fade-in zoom-in-95 duration-300">
                                    <div className="bg-zinc-950/50 border border-zinc-800 p-3 rounded-lg text-center">
                                        <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1">Framework</div>
                                        <div className="text-blue-400 font-bold text-sm" title={result.audit.framework}>{result.audit.framework || "Unknown"}</div>
                                    </div>
                                    <div className="bg-zinc-950/50 border border-zinc-800 p-3 rounded-lg text-center">
                                        <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1">VRAM</div>
                                        <div className="text-purple-400 font-bold text-sm">{result.audit.vram_min_gb ? `${result.audit.vram_min_gb} GB` : "N/A"}</div>
                                    </div>
                                    <div className="bg-zinc-950/50 border border-zinc-800 p-3 rounded-lg text-center">
                                        <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1">GPU</div>
                                        <div className="text-emerald-400 font-bold text-xs sm:text-sm">
                                            {(result.market_recommendations && result.market_recommendations[0]?.gpu_model) || "Flex"}
                                        </div>
                                    </div>
                                    <div className="bg-zinc-950/50 border border-zinc-800 p-3 rounded-lg text-center">
                                        <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1">Setup</div>
                                        <div className="text-yellow-400 font-bold text-sm">{result.environment?.estimated_setup_time_min || 5} min</div>
                                    </div>
                                    <div className="bg-zinc-950/50 border border-zinc-800 p-3 rounded-lg text-center">
                                        <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1">Health</div>
                                        <div className={`font-bold text-sm ${(result.audit.health_score || 80) >= 80 ? 'text-emerald-400' :
                                            (result.audit.health_score || 80) >= 60 ? 'text-yellow-400' : 'text-red-400'
                                            }`}>
                                            {result.audit.health_score || 100}/100
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Audit Results */}
                            {result?.audit && (
                                <Card className="bg-zinc-900/50 border-zinc-800 animate-in slide-in-from-right-4 duration-500">

                                    <CardHeader className="pb-2 cursor-pointer" onClick={() => setShowAuditDetails(!showAuditDetails)}>
                                        <CardTitle className="flex items-center gap-2 text-sm">
                                            <Brain className="w-4 h-4 text-yellow-400" />
                                            Kod Denetimi Sonuçları
                                            {showAuditDetails ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                                        </CardTitle>
                                    </CardHeader>
                                    {showAuditDetails && (
                                        <CardContent className="space-y-3">
                                            {result.audit.critical_issues?.length > 0 && (
                                                <div className="bg-red-500/10 p-3 rounded-md border border-red-500/20">
                                                    <h4 className="text-red-400 font-semibold mb-2 flex items-center gap-1 text-xs">
                                                        <AlertCircle className="h-3 w-3" /> Kritik Sorunlar ({result.audit.critical_issues.length})
                                                    </h4>
                                                    <ul className="list-disc list-inside text-xs space-y-1 text-red-300">
                                                        {result.audit.critical_issues.map((issue: string, i: number) => <li key={i}>{issue}</li>)}
                                                    </ul>
                                                </div>
                                            )}
                                            {result.audit.suggestions?.length > 0 && (
                                                <div className="bg-blue-500/10 p-3 rounded-md border border-blue-500/20">
                                                    <h4 className="text-blue-400 font-semibold mb-2 text-xs">💡 Öneriler</h4>
                                                    <ul className="list-disc list-inside text-xs space-y-1 text-blue-300">
                                                        {result.audit.suggestions.map((s: string, i: number) => <li key={i}>{s}</li>)}
                                                    </ul>
                                                </div>
                                            )}
                                        </CardContent>
                                    )}
                                </Card>
                            )}

                            {/* Environment */}
                            {result?.environment && (
                                <Card className="bg-zinc-900/50 border-zinc-800">
                                    <CardHeader className="pb-2 cursor-pointer" onClick={() => setShowEnvDetails(!showEnvDetails)}>
                                        <CardTitle className="flex items-center gap-2 text-sm">
                                            <Package className="w-4 h-4 text-purple-400" />
                                            Ortam Gereksinimleri
                                            {showEnvDetails ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                                        </CardTitle>
                                    </CardHeader>
                                    {showEnvDetails && (
                                        <CardContent className="space-y-3">
                                            <div className="font-mono text-xs bg-zinc-950 p-2 rounded border border-zinc-800">
                                                <span className="text-purple-400">FROM</span> <span className="text-emerald-400">{result.environment.base_image}</span>
                                            </div>
                                            {result.environment.python_packages?.length > 0 && (
                                                <div>
                                                    <p className="text-xs text-zinc-400 mb-2">Python Paketleri:</p>
                                                    <div className="flex flex-wrap gap-1">
                                                        {result.environment.python_packages.map((pkg: string, i: number) => (
                                                            <span key={i} className="px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded text-[10px] font-mono">{pkg}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            <div className="grid grid-cols-2 gap-2 text-xs">
                                                <div className="text-center p-2 bg-zinc-800/50 rounded">
                                                    <div className="text-zinc-500">CUDA</div>
                                                    <div className="font-bold text-white">{result.environment.cuda_version || "N/A"}</div>
                                                </div>
                                                <div className="text-center p-2 bg-zinc-800/50 rounded">
                                                    <div className="text-zinc-500">Kurulum Süresi</div>
                                                    <div className="font-bold text-white">{result.environment.estimated_setup_time_min}dk</div>
                                                </div>
                                            </div>
                                        </CardContent>
                                    )}
                                </Card>
                            )}

                            {/* Completion Action */}
                            {result && (
                                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                                    <h3 className="text-emerald-400 font-bold flex items-center gap-2 mb-2">
                                        <CheckCircle2 className="w-5 h-5" />
                                        Analiz Tamamlandı
                                    </h3>
                                    <p className="text-zinc-300 text-sm mb-3">
                                        <span className="font-bold text-white">{result.market_recommendations?.length || 0}</span> uygun GPU seçeneği bulundu.
                                    </p>
                                    <Button
                                        onClick={() => onComplete(code, result, fileInfo)}
                                        className="w-full bg-emerald-600 hover:bg-emerald-500"
                                    >
                                        GPU Önerilerini İncele & Seç
                                        <ArrowRight className="ml-2 w-4 h-4" />
                                    </Button>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="h-full flex items-center justify-center text-zinc-500 border border-zinc-800 rounded-lg bg-zinc-900/20">
                            <div className="text-center p-8">
                                <Activity className="w-12 h-12 mx-auto mb-4 opacity-20" />
                                <h3 className="text-lg font-medium text-zinc-300 mb-2">Analiz Bekleniyor</h3>
                                <p className="text-sm max-w-xs mx-auto">Python kodunuzu yükleyin ve "Analizi Başlat" butonuna tıklayın.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
