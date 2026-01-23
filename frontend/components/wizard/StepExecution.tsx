"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Loader2, Play, CheckCircle2, Info, ChevronDown, ChevronUp, AlertTriangle, XCircle, ArrowLeft, DollarSign, StopCircle } from "lucide-react"
import CostDisplay from "@/components/wizard/CostDisplay"
import ExecutionReport from "@/components/wizard/ExecutionReport"
import { useCostTracker } from "@/hooks/useCostTracker"
import { ExecutionReport as ExecutionReportType } from "@/lib/wizard-types"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = NEXT_PUBLIC_API_URL.replace("http", "ws")

interface StepExecutionProps {
    deploymentConfig: { sshConfig: any, fileInfo: any }
    selectedGpu?: any
    onBack: () => void
    onRestart?: () => void
}

export default function StepExecution({ deploymentConfig, selectedGpu, onBack, onRestart }: StepExecutionProps) {
    const [running, setRunning] = useState(false)
    const [logs, setLogs] = useState<string[]>([])
    const [showPreview, setShowPreview] = useState(true)
    const [executionStarted, setExecutionStarted] = useState(false)
    const [executionCompleted, setExecutionCompleted] = useState(false)
    const [report, setReport] = useState<ExecutionReportType | null>(null)
    const [budgetLimit, setBudgetLimit] = useState<number>(1.00) // Default $1 budget
    const logEndRef = useRef<HTMLDivElement>(null)
    const startTimeRef = useRef<Date | null>(null)

    const { sshConfig, fileInfo } = deploymentConfig
    const pricePerHour = selectedGpu?.price_hourly || 0.5

    // Cost tracker
    const costTracker = useCostTracker({
        pricePerHour,
        budgetLimit,
        onBudgetExceeded: (cost) => {
            setLogs(prev => [...prev, `⚠️ BÜTÇE UYARISI: Maliyet $${cost.toFixed(4)} - Limit: $${budgetLimit}`])
        }
    })

    const [showConfirmModal, setShowConfirmModal] = useState(false)

    // ... (keep costTracker)

    const handleExecute = async () => {
        setShowConfirmModal(true)
    }

    const startExecution = async () => {
        setRunning(true)
        setExecutionStarted(true)
        startTimeRef.current = new Date()
        costTracker.startTracking()
        setLogs(prev => [...prev, "🚀 Uzak sunucuya bağlanılıyor..."])

        try {
            // Common SSH + Auth params
            const baseBody: any = {
                hostname: sshConfig.hostname,
                username: sshConfig.username,
                port: sshConfig.port || 22,
                auth_type: sshConfig.authType || "key",
            };

            if (sshConfig.authType === "password") {
                baseBody.password = sshConfig.password;
            } else {
                baseBody.private_key = sshConfig.privateKey;
                if (sshConfig.passphrase) baseBody.passphrase = sshConfig.passphrase;
            }

            let endpoint = "";
            let body = { ...baseBody };
            let wsEndpointDescriptor = "";

            if (fileInfo.isProject) {
                // Project Deployment
                endpoint = "/v1/deploy/project";
                body.project_dir = fileInfo.local_path;
                body.entry_point = fileInfo.entry_point || "main.py"; // Default fallback
                body.install_requirements = true;
                wsEndpointDescriptor = "execute-project";

                setLogs(prev => [...prev, `📦 Proje modu: ${fileInfo.entry_point}`])
            } else {
                // Single Script Deployment
                endpoint = "/v1/deploy/execute";
                body.script_path = fileInfo.local_path;
                wsEndpointDescriptor = "execute";

                setLogs(prev => [...prev, `📄 Script modu: ${fileInfo.filename}`])
            }

            setLogs(prev => [...prev, "📤 İstek gönderiliyor..."])

            const token = localStorage.getItem("token")
            const headers: any = { 'Content-Type': 'application/json' }
            if (token) headers["Authorization"] = `Bearer ${token}`

            const res = await fetch(`${NEXT_PUBLIC_API_URL}${endpoint}`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(body)
            })

            if (res.ok) {
                const data = await res.json()
                setLogs(prev => [...prev, `✅ Job oluşturuldu: ${data.job_id}`, "📡 Canlı log akışı başlatılıyor..."])

                const ws = new WebSocket(`${WS_URL}/ws/${wsEndpointDescriptor}/${data.job_id}`)
                ws.onmessage = (e) => setLogs(prev => [...prev, e.data])
                ws.onclose = () => {
                    handleExecutionComplete(data.job_id)
                }
                ws.onerror = () => setLogs(prev => [...prev, "❌ WebSocket bağlantı hatası"])
            } else {
                const err = await res.json()
                setLogs(prev => [...prev, `❌ Hata: ${err.detail}`])
                setRunning(false)
                costTracker.stopTracking()
            }
        } catch (e) {
            setLogs(prev => [...prev, `❌ İstek hatası: ${e}`])
            setRunning(false)
            costTracker.stopTracking()
        }
    }

    const handleExecutionComplete = (jobId: string) => {
        setRunning(false)
        costTracker.stopTracking()

        // Use setTimeout to ensure state has settled before creating report
        setTimeout(() => {
            const endTime = new Date()
            const durationSeconds = startTimeRef.current
                ? Math.floor((endTime.getTime() - startTimeRef.current.getTime()) / 1000)
                : costTracker.elapsedSeconds

            // Calculate cost based on actual elapsed time
            const finalCost = (durationSeconds / 3600) * pricePerHour

            // Create report with current values
            const executionReport: ExecutionReportType = {
                jobId,
                gpu: selectedGpu?.gpu_model || 'Unknown GPU',
                startTime: startTimeRef.current?.toISOString() || new Date().toISOString(),
                endTime: endTime.toISOString(),
                durationSeconds,
                totalCost: finalCost > 0 ? finalCost : costTracker.currentCost,
                exitCode: 0,
                logsCount: 0, // Will be set from actual logs in ExecutionReport
                status: 'success'
            }

            setReport(executionReport)
            setExecutionCompleted(true)
            setLogs(prev => [...prev, "", "═".repeat(60), "✨ Çalıştırma tamamlandı!", "═".repeat(60)])
        }, 100)
    }

    const handleRerun = () => {
        setExecutionCompleted(false)
        setExecutionStarted(false)
        setReport(null)
        setLogs([])
        costTracker.resetTracking()
        setShowPreview(true)
    }

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [logs])

    return (
        <div className="h-full flex flex-col p-6 space-y-4">
            {/* Info Banner */}
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <h3 className="font-semibold text-emerald-200 mb-1">Adım 4: Çalıştırma & İzleme</h3>
                        <p className="text-sm text-emerald-300/90">
                            Script uzak GPU sunucusunda çalıştırılacak. Tüm çıktıları canlı olarak göreceksiniz.
                        </p>
                    </div>
                </div>
            </div>

            {/* Show Report if completed */}
            {executionCompleted && report ? (
                <ExecutionReport
                    report={report}
                    logs={logs}
                    onRerun={handleRerun}
                    onNewJob={onRestart || (() => window.location.reload())}
                />
            ) : (
                <>
                    {/* Pre-Execution Preview */}
                    {!executionStarted && (
                        <Card className="bg-zinc-900/50 border-zinc-800">
                            <CardHeader className="cursor-pointer" onClick={() => setShowPreview(!showPreview)}>
                                <CardTitle className="flex items-center gap-2 text-base">
                                    <Terminal className="w-5 h-5 text-blue-400" />
                                    Çalıştırılacak İşlem Özeti
                                    {showPreview ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                                </CardTitle>
                            </CardHeader>
                            {showPreview && (
                                <CardContent className="space-y-4">
                                    <div className="space-y-3 text-sm">
                                        <div className="grid grid-cols-2 gap-3">
                                            <div className="p-3 bg-zinc-950/50 rounded border border-zinc-800">
                                                <div className="text-zinc-500 text-xs mb-1">SUNUCU</div>
                                                <div className="font-mono text-zinc-200">{sshConfig.username}@{sshConfig.hostname}:{sshConfig.port}</div>
                                            </div>
                                            <div className="p-3 bg-zinc-950/50 rounded border border-zinc-800">
                                                <div className="text-zinc-500 text-xs mb-1">DOSYA</div>
                                                <div className="flex items-center justify-between">
                                                    <span className="font-mono text-zinc-200 text-sm">{fileInfo.filename}</span>
                                                    <span className="text-xs text-zinc-500">{(fileInfo.size / 1024).toFixed(1)} KB</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Budget Setting */}
                                        <div className="p-3 bg-zinc-950/50 rounded border border-zinc-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="text-zinc-500 text-xs">BÜTÇE LİMİTİ</div>
                                                <div className="flex items-center gap-2">
                                                    <input
                                                        type="number"
                                                        step="0.1"
                                                        min="0.1"
                                                        value={budgetLimit}
                                                        onChange={(e) => setBudgetLimit(parseFloat(e.target.value) || 1)}
                                                        className="w-20 h-7 bg-zinc-900 border border-zinc-700 rounded px-2 text-sm font-mono text-right"
                                                    />
                                                    <span className="text-zinc-400 text-sm">USD</span>
                                                </div>
                                            </div>
                                            <p className="text-[10px] text-zinc-500">Limit aşıldığında uyarı alırsınız (otomatik durdurma yok)</p>
                                        </div>

                                        <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded">
                                            <div className="flex items-start gap-2">
                                                <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                                                <div className="text-xs text-yellow-300">
                                                    <strong>Maliyet:</strong> ${pricePerHour.toFixed(2)}/saat.
                                                    Canlı maliyet takibi ile harcamanızı izleyebilirsiniz.
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex gap-2 pt-2 border-t border-zinc-800">
                                        <Button variant="outline" onClick={onBack} className="flex-1">
                                            <ArrowLeft className="w-4 h-4 mr-2" />
                                            Geri Dön
                                        </Button>
                                        <Button
                                            onClick={handleExecute}
                                            className="flex-1 bg-emerald-600 hover:bg-emerald-500"
                                        >
                                            <Play className="w-4 h-4 mr-2" />
                                            Çalıştırmayı Başlat
                                        </Button>
                                    </div>
                                </CardContent>
                            )}
                        </Card>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
                        {/* Console Output */}
                        <Card className="lg:col-span-2 bg-zinc-950 border border-zinc-800 flex flex-col min-h-[400px]">
                            <CardHeader className="py-3 px-4 border-b border-zinc-800 bg-zinc-900/50">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-sm text-zinc-400">
                                        <Terminal className="w-4 h-4" />
                                        Konsol Çıktısı
                                    </div>
                                    {running && (
                                        <div className="flex items-center gap-2 px-2 py-1 bg-blue-500/10 rounded text-xs text-blue-400">
                                            <Loader2 className="w-3 h-3 animate-spin" /> Çalışıyor
                                        </div>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1">
                                {logs.length === 0 ? (
                                    <div className="h-full flex flex-col items-center justify-center text-zinc-600">
                                        <Play className="w-12 h-12 mb-4 opacity-20" />
                                        <p>Çalıştırmayı başlatmak için yukarıdaki butona tıklayın</p>
                                    </div>
                                ) : (
                                    logs.map((line, i) => (
                                        <div key={i} className={`break-all leading-relaxed ${line.startsWith("❌") ? "text-red-400" :
                                            line.startsWith("✅") || line.startsWith("✨") ? "text-emerald-400 font-bold" :
                                                line.startsWith("🚀") || line.startsWith("═") ? "text-blue-400 font-bold" :
                                                    line.startsWith("⚠️") ? "text-yellow-400" :
                                                        "text-zinc-300"
                                            }`}>
                                            {line}
                                        </div>
                                    ))
                                )}
                                <div ref={logEndRef} />
                            </CardContent>
                        </Card>

                        {/* Cost Display Sidebar */}
                        {executionStarted && (
                            <div className="space-y-4">
                                <CostDisplay
                                    isTracking={costTracker.isTracking}
                                    formattedTime={costTracker.formattedTime}
                                    formattedCost={costTracker.formattedCost}
                                    currentCost={costTracker.currentCost}
                                    pricePerHour={pricePerHour}
                                    budgetLimit={budgetLimit}
                                    budgetWarning={costTracker.budgetWarning}
                                />

                                {running && (
                                    <Button
                                        variant="outline"
                                        className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10"
                                        onClick={() => {
                                            // In real app, would call backend to stop job
                                            setRunning(false)
                                            costTracker.stopTracking()
                                            setLogs(prev => [...prev, "⛔ İşlem kullanıcı tarafından durduruldu"])
                                        }}
                                    >
                                        <StopCircle className="w-4 h-4 mr-2" />
                                        Durdur
                                    </Button>
                                )}
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* Confirmation Modal */}
            {showConfirmModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-lg max-w-sm w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95">
                        <div className="flex flex-col items-center text-center space-y-2">
                            <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center mb-2">
                                <Play className="w-6 h-6 text-blue-400" />
                            </div>
                            <h3 className="text-lg font-bold text-white">Çalıştırmayı Başlat?</h3>
                            <div className="text-sm text-zinc-400">
                                <p>"{fileInfo.filename}" scripti seçilen GPU sunucusunda çalıştırılacak.</p>
                                <p className="mt-2 text-yellow-500/80">⚠️ Saatlik maliyet işlemeye başlayacaktır.</p>
                            </div>
                        </div>
                        <div className="flex gap-3 pt-2">
                            <Button variant="outline" className="flex-1" onClick={() => setShowConfirmModal(false)}>
                                İptal
                            </Button>
                            <Button className="flex-1 bg-blue-600 hover:bg-blue-500" onClick={() => { setShowConfirmModal(false); startExecution(); }}>
                                Başlat (${pricePerHour}/saat)
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
