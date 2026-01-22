"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Loader2, Play, CheckCircle2, Info, ChevronDown, ChevronUp, AlertTriangle, XCircle, ArrowLeft, DollarSign } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = NEXT_PUBLIC_API_URL.replace("http", "ws")

interface StepExecutionProps {
    deploymentConfig: { sshConfig: any, fileInfo: any }
    onBack: () => void
}

export default function StepExecution({ deploymentConfig, onBack }: StepExecutionProps) {
    const [running, setRunning] = useState(false)
    const [logs, setLogs] = useState<string[]>([])
    const [showPreview, setShowPreview] = useState(true)
    const [showConfirmation, setShowConfirmation] = useState(true)
    const [executionStarted, setExecutionStarted] = useState(false)
    const logEndRef = useRef<HTMLDivElement>(null)

    const { sshConfig, fileInfo } = deploymentConfig

    const handleExecute = async () => {
        if (!showConfirmation) {
            startExecution()
            return
        }

        // Show browser confirmation
        if (window.confirm("Kod çalıştırma işlemi başlayacak. Devam etmek istiyor musunuz?")) {
            startExecution()
        }
    }

    const startExecution = async () => {
        setRunning(true)
        setExecutionStarted(true)
        setLogs(prev => [...prev, "🚀 Uzak sunucuya bağlanılıyor..."])

        try {
            const body: any = {
                hostname: sshConfig.hostname,
                username: sshConfig.username,
                port: sshConfig.port || 22,
                auth_type: sshConfig.authType || "key",
                script_path: fileInfo.local_path
            };

            if (sshConfig.authType === "password") {
                body.password = sshConfig.password;
            } else {
                body.private_key = sshConfig.privateKey;
                if (sshConfig.passphrase) body.passphrase = sshConfig.passphrase;
            }

            setLogs(prev => [...prev, "📤 İstek gönderiliyor..."])

            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/deploy/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            })

            if (res.ok) {
                const data = await res.json()
                setLogs(prev => [...prev, `✅ Job oluşturuldu: ${data.job_id}`, "📡 Canlı log akışı başlatılıyor..."])

                const ws = new WebSocket(`${WS_URL}/ws/execute/${data.job_id}`)
                ws.onmessage = (e) => setLogs(prev => [...prev, e.data])
                ws.onclose = () => {
                    setRunning(false)
                    setLogs(prev => [...prev, "", "═".repeat(60), "✨ Çalıştırma tamamlandı!", "═".repeat(60)])
                }
                ws.onerror = () => setLogs(prev => [...prev, "❌ WebSocket bağlantı hatası"])
            } else {
                const err = await res.json()
                setLogs(prev => [...prev, `❌ Hata: ${err.detail}`])
                setRunning(false)
            }
        } catch (e) {
            setLogs(prev => [...prev, `❌ İstek hatası: ${e}`])
            setRunning(false)
        }
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

                                <div className="p-3 bg-zinc-950/50 rounded border border-zinc-800">
                                    <div className="text-zinc-500 text-xs mb-1">YAPILACAK İŞLEMLER</div>
                                    <ul className="text-xs space-y-1 text-zinc-300">
                                        <li>1. SSH bağlantısı kurulacak</li>
                                        <li>2. Dosya uzak sunucuya kopyalanacak</li>
                                        <li>3. Python script çalıştırılacak</li>
                                        <li>4. Çıktılar canlı olarak gösterilecek</li>
                                    </ul>
                                </div>

                                <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded">
                                    <div className="flex items-start gap-2">
                                        <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                                        <div className="text-xs text-yellow-300">
                                            <strong>Maliyet Uyarısı:</strong> Bu işlem GPU kullanımı başlatacak.
                                            Tahmini maliyet: <strong>${sshConfig.estimatedCost || "değişken"}/saat</strong>.
                                            İşlemi istediğiniz zaman durdurabilirsiniz.
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

            {/* Console Output */}
            <Card className="flex-1 bg-zinc-950 border border-zinc-800 flex flex-col min-h-[400px]">
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
                        {!running && logs.length > 0 && (
                            <div className="flex items-center gap-2 px-2 py-1 bg-emerald-500/10 rounded text-xs text-emerald-400">
                                <CheckCircle2 className="w-3 h-3" /> Tamamlandı
                            </div>
                        )}
                    </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1">
                    {logs.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-zinc-600">
                            <Play className="w-12 h-12 mb-4 opacity-20" />
                            <p>Çalıştırmayı başlatmak için yukarıdaki butona tıklayın</p>
                            <p className="text-xs mt-2">Tüm işlemler ve çıktılar burada görünecek</p>
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

            {/* Post-execution Actions */}
            {!running && logs.length > 0 && (
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setLogs([])} className="flex-1">
                        Konsolu Temizle
                    </Button>
                    <Button variant="outline" onClick={onBack} className="flex-1">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Önceki Adıma Dön
                    </Button>
                </div>
            )}
        </div>
    )
}
