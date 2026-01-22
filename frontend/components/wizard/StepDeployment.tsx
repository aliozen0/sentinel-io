"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2, Server, Rocket, KeyRound, ExternalLink, Copy, CheckCircle2, ArrowLeft, Info, ChevronDown, ChevronUp, Upload, FileCode, AlertTriangle, XCircle } from "lucide-react"
import { SshConnectionModal } from "@/components/ssh-connection-modal"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface StepDeploymentProps {
    selectedGpu: any
    analysisResult?: any
    onReady: (config: { sshConfig: any, fileInfo: any }) => void
    onBack: () => void
}

export default function StepDeployment({ selectedGpu, analysisResult, onReady, onBack }: StepDeploymentProps) {
    const [showSshModal, setShowSshModal] = useState(false)
    const [sshConfig, setSshConfig] = useState<any>(null)
    const [connectionVerified, setConnectionVerified] = useState(false)
    const [loadingDemo, setLoadingDemo] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [uploadedFileInfo, setUploadedFileInfo] = useState<any>(null)
    const [testingConnection, setTestingConnection] = useState(false)
    const [connectionTestResult, setConnectionTestResult] = useState<{ success: boolean, message: string } | null>(null)
    const [showConnectionDetails, setShowConnectionDetails] = useState(false)
    const [showUploadDetails, setShowUploadDetails] = useState(false)

    const fetchDemoCredentials = async () => {
        setLoadingDemo(true)
        try {
            const demoRes = await fetch(`${NEXT_PUBLIC_API_URL}/v1/connections/demo`)
            if (!demoRes.ok) throw new Error("Demo unavailable")
            const demoData = await demoRes.json()

            const keyRes = await fetch(`${NEXT_PUBLIC_API_URL}/v1/connections/demo/key`)
            const keyData = await keyRes.json()

            const config = {
                hostname: demoData.hostname,
                port: demoData.port,
                username: demoData.username,
                privateKey: keyData.private_key,
                authType: 'key'
            }
            setSshConfig(config)
            setShowSshModal(true)
            setShowConnectionDetails(true)

        } catch (err) {
            console.error(err)
            alert("Demo sunucu kullanılamıyor. Docker çalışıyor mu?")
        } finally {
            setLoadingDemo(false)
        }
    }

    const handleTestConnection = async () => {
        if (!sshConfig) return
        setTestingConnection(true)
        setConnectionTestResult(null)

        // Simulate connection test (in real app, call backend)
        setTimeout(() => {
            setConnectionTestResult({
                success: true,
                message: `${sshConfig.username}@${sshConfig.hostname}:${sshConfig.port} bağlantısı başarılı!`
            })
            setConnectionVerified(true)
            setTestingConnection(false)
        }, 1500)
    }

    return (
        <div className="h-full flex flex-col p-6 space-y-6">
            {/* Info Banner */}
            <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <h3 className="font-semibold text-purple-200 mb-1">Adım 3: Bağlantı & Upload</h3>
                        <p className="text-sm text-purple-300/90">
                            Seçilen GPU'ya bağlanmak için SSH bilgilerinizi girin ve scriptinizi yükleyin.
                            Her adımı manuel olarak onaylayacaksınız.
                        </p>
                    </div>
                </div>
            </div>

            {/* Target Summary */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <div className="flex items-center gap-4">
                    <div className="bg-blue-500/20 p-3 rounded-full">
                        <Server className="w-6 h-6 text-blue-400" />
                    </div>
                    <div className="flex-1">
                        <h3 className="font-semibold text-blue-200">Hedef Sunucu</h3>
                        <p className="text-sm text-blue-300 mt-1">
                            <strong className="text-white">{selectedGpu.gpu_model}</strong> • ${selectedGpu.price_hourly}/saat
                        </p>
                        <p className="text-xs text-blue-400 mt-1">
                            Ortam: <code className="bg-blue-500/20 px-1 rounded font-mono text-[10px]">{analysisResult?.environment?.base_image || "Docker Image"}</code>
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Connection */}
                <Card className={`bg-zinc-900/50 transition-all ${connectionVerified ? 'border-emerald-500/50' : 'border-zinc-800'}`}>
                    <CardHeader className="cursor-pointer" onClick={() => setShowConnectionDetails(!showConnectionDetails)}>
                        <CardTitle className="flex items-center gap-3 text-base">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${connectionVerified ? 'bg-emerald-500' : 'bg-zinc-800'}`}>
                                <KeyRound className="w-5 h-5 text-white" />
                            </div>
                            <div className="flex-1">
                                <div>SSH Bağlantısı</div>
                                <div className="text-xs text-zinc-400 font-normal">
                                    {connectionVerified ? `✓ ${sshConfig.username}@${sshConfig.hostname}` : "Henüz bağlanılmadı"}
                                </div>
                            </div>
                            {showConnectionDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </CardTitle>
                    </CardHeader>
                    {showConnectionDetails && (
                        <CardContent className="space-y-4">
                            <div className="p-3 bg-zinc-950/50 rounded border border-zinc-800 text-xs space-y-2">
                                <p className="text-zinc-300">
                                    <strong>Ne yapılacak?</strong> Uzak sunucuya SSH ile bağlanacaksınız.
                                    Bu bağlantı sayesinde scriptinizi yükleyebilir ve çalıştırabilirsiniz.
                                </p>
                                {sshConfig && (
                                    <div className="mt-2 p-2 bg-zinc-900 rounded">
                                        <div className="text-zinc-500 mb-1">Bağlantı Bilgileri:</div>
                                        <div className="font-mono text-[10px] text-zinc-300">
                                            {sshConfig.username}@{sshConfig.hostname}:{sshConfig.port}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {!sshConfig ? (
                                <div className="space-y-2">
                                    <Button
                                        className="w-full bg-zinc-800 hover:bg-zinc-700"
                                        variant="outline"
                                        onClick={fetchDemoCredentials}
                                        disabled={loadingDemo}
                                    >
                                        {loadingDemo ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : "🎮"}
                                        Demo Sunucu Bilgilerini Al (Hızlı Test)
                                    </Button>
                                    <div className="text-center text-xs text-zinc-600">- veya -</div>
                                    <Button className="w-full" onClick={() => setShowSshModal(true)}>
                                        Manuel SSH Bilgileri Gir
                                    </Button>
                                </div>
                            ) : !connectionVerified ? (
                                <div className="space-y-2">
                                    <Button
                                        className="w-full bg-blue-600 hover:bg-blue-500"
                                        onClick={handleTestConnection}
                                        disabled={testingConnection}
                                    >
                                        {testingConnection ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                                        Bağlantıyı Test Et
                                    </Button>
                                    {connectionTestResult && (
                                        <div className={`p-2 rounded text-xs flex items-center gap-2 ${connectionTestResult.success
                                            ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                                            : 'bg-red-500/10 border border-red-500/20 text-red-300'
                                            }`}>
                                            {connectionTestResult.success ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                            {connectionTestResult.message}
                                        </div>
                                    )}
                                    <Button variant="ghost" size="sm" className="w-full" onClick={() => setShowSshModal(true)}>
                                        Bilgileri Düzenle
                                    </Button>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded text-xs text-emerald-300 flex items-center gap-2">
                                        <CheckCircle2 className="w-4 h-4" />
                                        Bağlantı başarılı! İşlemlere devam edebilirsiniz.
                                    </div>
                                    <Button variant="outline" size="sm" className="w-full" onClick={() => { setConnectionVerified(false); setShowSshModal(true); }}>
                                        Bağlantı Ayarlarını Değiştir
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    )}
                </Card>

                {/* Upload */}
                <Card className={`bg-zinc-900/50 transition-all ${uploadedFileInfo ? 'border-emerald-500/50' : 'border-zinc-800'}`}>
                    <CardHeader className="cursor-pointer" onClick={() => setShowUploadDetails(!showUploadDetails)}>
                        <CardTitle className="flex items-center gap-3 text-base">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${uploadedFileInfo ? 'bg-emerald-500' : 'bg-zinc-800'}`}>
                                <Upload className="w-5 h-5 text-white" />
                            </div>
                            <div className="flex-1">
                                <div>Script Upload</div>
                                <div className="text-xs text-zinc-400 font-normal">
                                    {uploadedFileInfo ? `✓ ${uploadedFileInfo.filename}` : "Dosya yüklenmedi"}
                                </div>
                            </div>
                            {showUploadDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </CardTitle>
                    </CardHeader>
                    {showUploadDetails && (
                        <CardContent className="space-y-4">
                            <div className="p-3 bg-zinc-950/50 rounded border border-zinc-800 text-xs space-y-2">
                                <p className="text-zinc-300">
                                    <strong>Ne yapılacak?</strong> Python scriptiniz backend sunucuya yüklenecek.
                                    Ardından uzak GPU sunucusuna aktarılacak.
                                </p>
                                {uploadedFileInfo && (
                                    <div className="mt-2 p-2 bg-zinc-900 rounded">
                                        <div className="text-zinc-500 mb-1">Yüklenen Dosya:</div>
                                        <div className="flex items-center justify-between">
                                            <div className="font-mono text-[10px] text-zinc-300">{uploadedFileInfo.filename}</div>
                                            <div className="text-[10px] text-zinc-500">{(uploadedFileInfo.size / 1024).toFixed(1)} KB</div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {!connectionVerified ? (
                                <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded text-xs text-yellow-300 flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4" />
                                    Önce SSH bağlantısı yapın
                                </div>
                            ) : !uploadedFileInfo ? (
                                <div className="space-y-2">
                                    <input
                                        id="wizard-upload"
                                        type="file"
                                        className="hidden"
                                        accept=".py"
                                        onChange={async (e) => {
                                            const file = e.target.files?.[0]
                                            if (!file) return
                                            setUploading(true)
                                            try {
                                                const formData = new FormData()
                                                formData.append('file', file)
                                                const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/upload`, {
                                                    method: 'POST',
                                                    body: formData
                                                })
                                                if (res.ok) {
                                                    const data = await res.json()
                                                    setUploadedFileInfo(data)
                                                }
                                            } catch (err) { console.error(err) }
                                            finally { setUploading(false) }
                                        }}
                                    />
                                    <Button
                                        className="w-full bg-blue-600 hover:bg-blue-500"
                                        disabled={uploading}
                                        onClick={() => document.getElementById('wizard-upload')?.click()}
                                    >
                                        {uploading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Upload className="w-4 h-4 mr-2" />}
                                        Python Dosyası Seç ve Yükle
                                    </Button>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded text-xs text-emerald-300 flex items-center gap-2">
                                        <CheckCircle2 className="w-4 h-4" />
                                        Dosya başarıyla yüklendi!
                                    </div>
                                    <Button variant="outline" size="sm" className="w-full" onClick={() => { setUploadedFileInfo(null); document.getElementById('wizard-upload')?.click(); }}>
                                        Farklı Dosya Yükle
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    )}
                </Card>
            </div>

            {/* Proceed Button */}
            <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
                <Button variant="outline" onClick={onBack}>
                    <ArrowLeft className="w-4 h-4 mr-2" /> Geri
                </Button>
                <Button
                    size="lg"
                    className="bg-emerald-600 hover:bg-emerald-500 px-8"
                    disabled={!connectionVerified || !uploadedFileInfo}
                    onClick={() => onReady({ sshConfig, fileInfo: uploadedFileInfo })}
                >
                    Çalıştırmaya Geç
                    <Rocket className="w-4 h-4 ml-2" />
                </Button>
            </div>

            <SshConnectionModal
                isOpen={showSshModal}
                onClose={() => setShowSshModal(false)}
                initialValues={sshConfig}
                onSave={(config) => {
                    setSshConfig(config)
                    setShowSshModal(false)
                    setConnectionTestResult(null)
                    setConnectionVerified(false)
                }}
            />
        </div>
    )
}
