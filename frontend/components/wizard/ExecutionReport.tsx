"use client"

// Execution Report Component - Summary after job completion

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    CheckCircle2, XCircle, Clock, DollarSign, FileText,
    Download, RotateCcw, ChevronDown, ChevronUp, Terminal,
    Cpu, Activity
} from "lucide-react"
import { ExecutionReport as ExecutionReportType } from "@/lib/wizard-types"

interface ExecutionReportProps {
    report: ExecutionReportType
    logs: string[]
    onRerun: () => void
    onNewJob: () => void
}

export default function ExecutionReport({ report, logs, onRerun, onNewJob }: ExecutionReportProps) {
    const [showLogs, setShowLogs] = useState(false)

    const isSuccess = report.status === 'success'

    // Format duration
    const formatDuration = (seconds: number) => {
        const hrs = Math.floor(seconds / 3600)
        const mins = Math.floor((seconds % 3600) / 60)
        const secs = seconds % 60

        if (hrs > 0) return `${hrs}sa ${mins}dk ${secs}sn`
        if (mins > 0) return `${mins}dk ${secs}sn`
        return `${secs} saniye`
    }

    // Download logs as text file
    const downloadLogs = () => {
        const content = logs.join('\n')
        const blob = new Blob([content], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `execution-${report.jobId}.log`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    return (
        <div className="space-y-4">
            {/* Status Banner */}
            <div className={`rounded-lg p-4 border ${isSuccess
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-red-500/10 border-red-500/30'
                }`}>
                <div className="flex items-center gap-3">
                    {isSuccess
                        ? <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                        : <XCircle className="w-8 h-8 text-red-400" />
                    }
                    <div>
                        <h3 className={`text-lg font-bold ${isSuccess ? 'text-emerald-300' : 'text-red-300'}`}>
                            {isSuccess ? 'Çalıştırma Başarılı!' : 'Çalıştırma Başarısız'}
                        </h3>
                        <p className="text-sm text-zinc-400">
                            Job ID: <code className="font-mono text-xs bg-zinc-800 px-1 rounded">{report.jobId}</code>
                        </p>
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4 text-center">
                        <Cpu className="w-5 h-5 mx-auto mb-1 text-blue-400" />
                        <div className="text-lg font-bold text-white">{report.gpu}</div>
                        <div className="text-[10px] text-zinc-500 uppercase">GPU</div>
                    </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4 text-center">
                        <Clock className="w-5 h-5 mx-auto mb-1 text-purple-400" />
                        <div className="text-lg font-bold text-white">{formatDuration(report.durationSeconds)}</div>
                        <div className="text-[10px] text-zinc-500 uppercase">Toplam Süre</div>
                    </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4 text-center">
                        <DollarSign className="w-5 h-5 mx-auto mb-1 text-emerald-400" />
                        <div className="text-lg font-bold text-emerald-400">${report.totalCost.toFixed(4)}</div>
                        <div className="text-[10px] text-zinc-500 uppercase">Toplam Maliyet</div>
                    </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4 text-center">
                        <Activity className="w-5 h-5 mx-auto mb-1 text-yellow-400" />
                        <div className={`text-lg font-bold ${report.exitCode === 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {report.exitCode}
                        </div>
                        <div className="text-[10px] text-zinc-500 uppercase">Exit Code</div>
                    </CardContent>
                </Card>
            </div>

            {/* Timestamps */}
            <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <div className="text-zinc-500 text-xs">Başlangıç</div>
                            <div className="text-white font-mono text-xs">
                                {new Date(report.startTime).toLocaleString('tr-TR')}
                            </div>
                        </div>
                        <div>
                            <div className="text-zinc-500 text-xs">Bitiş</div>
                            <div className="text-white font-mono text-xs">
                                {new Date(report.endTime).toLocaleString('tr-TR')}
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Logs Section */}
            <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader
                    className="cursor-pointer py-3"
                    onClick={() => setShowLogs(!showLogs)}
                >
                    <CardTitle className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                            <Terminal className="w-4 h-4 text-zinc-400" />
                            <span>Loglar ({report.logsCount} satır)</span>
                        </div>
                        {showLogs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </CardTitle>
                </CardHeader>
                {showLogs && (
                    <CardContent className="pt-0">
                        <div className="bg-black rounded p-3 max-h-64 overflow-y-auto font-mono text-xs">
                            {logs.length === 0 ? (
                                <span className="text-zinc-500">Log bulunamadı</span>
                            ) : (
                                logs.map((log, i) => (
                                    <div key={i} className={`${log.startsWith('❌') ? 'text-red-400' :
                                            log.startsWith('✅') || log.startsWith('✨') ? 'text-emerald-400' :
                                                'text-zinc-300'
                                        }`}>
                                        {log}
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                )}
            </Card>

            {/* Actions */}
            <div className="flex gap-3">
                <Button
                    variant="outline"
                    className="flex-1"
                    onClick={downloadLogs}
                >
                    <Download className="w-4 h-4 mr-2" />
                    Logları İndir
                </Button>
                <Button
                    variant="outline"
                    className="flex-1"
                    onClick={onRerun}
                >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Tekrar Çalıştır
                </Button>
                <Button
                    className="flex-1 bg-blue-600 hover:bg-blue-500"
                    onClick={onNewJob}
                >
                    Yeni İş Başlat
                </Button>
            </div>
        </div>
    )
}
