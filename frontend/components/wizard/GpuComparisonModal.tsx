"use client"

// GPU Comparison Modal - Side-by-side GPU comparison with AI recommendation

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { X, Cpu, DollarSign, Gauge, HardDrive, Zap, Sparkles, ChevronDown, ChevronUp } from "lucide-react"

interface GpuComparisonModalProps {
    isOpen: boolean
    onClose: () => void
    gpus: any[]
    onSelect: (gpu: any) => void
    analysisResult?: any
}

export default function GpuComparisonModal({ isOpen, onClose, gpus, onSelect, analysisResult }: GpuComparisonModalProps) {
    const [showAiRecommendation, setShowAiRecommendation] = useState(false)

    if (!isOpen || gpus.length < 2) return null

    // Calculate comparison metrics
    const getMetrics = (gpu: any) => ({
        pricePerformance: (gpu.score / gpu.price_hourly).toFixed(2),
        dailyCost: (gpu.price_hourly * 24).toFixed(2),
        weeklyCost: (gpu.price_hourly * 24 * 7).toFixed(2),
        availability: `${gpu.idle_nodes}/${gpu.total_nodes}`
    })

    // Simple AI recommendation logic
    const getAiRecommendation = () => {
        const sorted = [...gpus].sort((a, b) => (b.score / b.price_hourly) - (a.score / a.price_hourly))
        const best = sorted[0]
        const cheapest = [...gpus].sort((a, b) => a.price_hourly - b.price_hourly)[0]
        const fastest = [...gpus].sort((a, b) => b.score - a.score)[0]

        return {
            bestValue: best,
            cheapest,
            fastest,
            recommendation: `En iyi fiyat/performans oranı için **${best.gpu_model}** önerilir. `
                + `En düşük maliyet istiyorsanız **${cheapest.gpu_model}** (${cheapest.price_hourly}$/sa), `
                + `en yüksek performans istiyorsanız **${fastest.gpu_model}** (Skor: ${fastest.score.toFixed(1)}) seçebilirsiniz.`
        }
    }

    const aiRec = getAiRecommendation()

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-5xl bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <Cpu className="w-5 h-5" />
                        GPU Karşılaştırma ({gpus.length} GPU)
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-white/20 rounded-full transition">
                        <X className="w-5 h-5 text-white" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-5 space-y-4">
                    {/* AI Recommendation */}
                    <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-lg p-4">
                        <button
                            onClick={() => setShowAiRecommendation(!showAiRecommendation)}
                            className="w-full flex items-center justify-between"
                        >
                            <div className="flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-purple-400" />
                                <span className="font-semibold text-purple-200">AI Öneri Asistanı</span>
                            </div>
                            {showAiRecommendation ? <ChevronUp className="w-4 h-4 text-purple-400" /> : <ChevronDown className="w-4 h-4 text-purple-400" />}
                        </button>
                        {showAiRecommendation && (
                            <div className="mt-3 space-y-3 text-sm">
                                <p className="text-purple-200 leading-relaxed">{aiRec.recommendation}</p>
                                <div className="grid grid-cols-3 gap-2">
                                    <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded text-center">
                                        <div className="text-[10px] text-emerald-400 uppercase">En İyi Değer</div>
                                        <div className="font-bold text-emerald-300">{aiRec.bestValue.gpu_model}</div>
                                    </div>
                                    <div className="p-2 bg-blue-500/10 border border-blue-500/20 rounded text-center">
                                        <div className="text-[10px] text-blue-400 uppercase">En Ucuz</div>
                                        <div className="font-bold text-blue-300">{aiRec.cheapest.gpu_model}</div>
                                    </div>
                                    <div className="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-center">
                                        <div className="text-[10px] text-yellow-400 uppercase">En Hızlı</div>
                                        <div className="font-bold text-yellow-300">{aiRec.fastest.gpu_model}</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Comparison Table */}
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-zinc-700">
                                    <th className="text-left py-3 px-4 text-zinc-400 font-medium">Özellik</th>
                                    {gpus.map((gpu, i) => (
                                        <th key={i} className="text-center py-3 px-4">
                                            <div className="flex flex-col items-center gap-1">
                                                <Cpu className={`w-5 h-5 ${i === 0 ? 'text-emerald-400' : 'text-zinc-400'}`} />
                                                <span className="font-bold text-white">{gpu.gpu_model}</span>
                                                {i === 0 && <span className="text-[10px] bg-emerald-500 text-white px-2 py-0.5 rounded">ÖNERİLEN</span>}
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-800">
                                <tr>
                                    <td className="py-3 px-4 text-zinc-400 flex items-center gap-2">
                                        <Gauge className="w-4 h-4" /> Skor
                                    </td>
                                    {gpus.map((gpu, i) => (
                                        <td key={i} className="py-3 px-4 text-center">
                                            <span className={`font-bold ${i === 0 ? 'text-emerald-400' : 'text-white'}`}>
                                                {gpu.score?.toFixed(1)}
                                            </span>
                                        </td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="py-3 px-4 text-zinc-400 flex items-center gap-2">
                                        <DollarSign className="w-4 h-4" /> Saatlik Ücret
                                    </td>
                                    {gpus.map((gpu, i) => (
                                        <td key={i} className="py-3 px-4 text-center">
                                            <span className="font-bold text-white">${gpu.price_hourly}</span>
                                        </td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="py-3 px-4 text-zinc-400 flex items-center gap-2">
                                        <DollarSign className="w-4 h-4" /> Günlük Maliyet
                                    </td>
                                    {gpus.map((gpu, i) => {
                                        const m = getMetrics(gpu)
                                        return (
                                            <td key={i} className="py-3 px-4 text-center text-zinc-300">
                                                ${m.dailyCost}
                                            </td>
                                        )
                                    })}
                                </tr>
                                <tr>
                                    <td className="py-3 px-4 text-zinc-400 flex items-center gap-2">
                                        <Zap className="w-4 h-4" /> Fiyat/Performans
                                    </td>
                                    {gpus.map((gpu, i) => {
                                        const m = getMetrics(gpu)
                                        return (
                                            <td key={i} className="py-3 px-4 text-center">
                                                <span className="text-purple-400 font-mono">{m.pricePerformance}</span>
                                            </td>
                                        )
                                    })}
                                </tr>
                                <tr>
                                    <td className="py-3 px-4 text-zinc-400 flex items-center gap-2">
                                        <HardDrive className="w-4 h-4" /> Müsaitlik
                                    </td>
                                    {gpus.map((gpu, i) => {
                                        const m = getMetrics(gpu)
                                        return (
                                            <td key={i} className="py-3 px-4 text-center">
                                                <span className={`font-mono ${gpu.idle_nodes > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                    {m.availability}
                                                </span>
                                            </td>
                                        )
                                    })}
                                </tr>
                                <tr>
                                    <td className="py-3 px-4 text-zinc-400">Güvenilirlik</td>
                                    {gpus.map((gpu, i) => (
                                        <td key={i} className="py-3 px-4 text-center">
                                            <span className={`font-mono ${gpu.reliability > 98 ? 'text-emerald-400' : 'text-yellow-400'}`}>
                                                {gpu.reliability}%
                                            </span>
                                        </td>
                                    ))}
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    {/* Action Buttons */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-4">
                        {gpus.map((gpu, i) => (
                            <Button
                                key={i}
                                onClick={() => { onSelect(gpu); onClose(); }}
                                className={`h-12 ${i === 0 ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-zinc-700 hover:bg-zinc-600'}`}
                            >
                                {gpu.gpu_model} Seç
                            </Button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
