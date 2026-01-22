"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Cpu, DollarSign, Server, ArrowLeft, ArrowRight, Check, ChevronRight, Info, ChevronDown, ChevronUp, Zap, HardDrive, Gauge } from "lucide-react"

interface StepGpuSelectionProps {
    analysisResult: any
    onSelect: (gpu: any) => void
    onBack: () => void
}

export default function StepGpuSelection({ analysisResult, onSelect, onBack }: StepGpuSelectionProps) {
    const [selectedForComparison, setSelectedForComparison] = useState<number | null>(null)
    const [showDetails, setShowDetails] = useState<number | null>(null)

    if (!analysisResult) return null

    const recommendedNodes = analysisResult.market_recommendations || []
    const summary = analysisResult.summary || {}

    return (
        <div className="h-full flex flex-col p-6 space-y-4">
            {/* Info Banner */}
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <h3 className="font-semibold text-emerald-200 mb-1">Adım 2: GPU Seçimi</h3>
                        <p className="text-sm text-emerald-300/90">
                            Kodunuz analiz edildi. Aşağıda <strong>{recommendedNodes.length} uygun GPU</strong> seçeneği gösteriliyor.
                            Her kartı inceleyerek gereksinimlerinize en uygun olanı seçin.
                        </p>
                    </div>
                </div>
            </div>

            {/* Analysis Summary */}
            <Card className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border-blue-500/30">
                <CardContent className="py-3">
                    <h4 className="text-xs text-blue-300 mb-2 font-semibold">📊 Analiz Özeti</h4>
                    <div className="grid grid-cols-5 gap-3 text-center">
                        <div>
                            <div className="text-[10px] text-zinc-400 uppercase">Framework</div>
                            <div className="font-bold text-sm text-blue-400">{summary.framework || "N/A"}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-zinc-400 uppercase">VRAM</div>
                            <div className="font-bold text-sm text-purple-400">{summary.vram_required || "N/A"}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-zinc-400 uppercase">Önerilen</div>
                            <div className="font-bold text-sm text-emerald-400">{summary.recommended_gpu || "N/A"}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-zinc-400 uppercase">Kurulum</div>
                            <div className="font-bold text-sm text-yellow-400">{summary.estimated_setup || "N/A"}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-zinc-400 uppercase">Skor</div>
                            <div className="font-bold text-sm text-emerald-400">{summary.health_score || "N/A"}/100</div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Uygun GPU Seçenekleri</h2>
                <Button variant="outline" onClick={onBack} size="sm">
                    <ArrowLeft className="w-4 h-4 mr-2" /> Geri
                </Button>
            </div>

            {/* GPU Cards */}
            <div className="grid grid-cols-1 gap-4 overflow-y-auto pb-4">
                {recommendedNodes.map((node: any, i: number) => {
                    const isExpanded = showDetails === i
                    const isRecommended = i === 0

                    return (
                        <Card
                            key={i}
                            className={`transition-all hover:shadow-lg relative overflow-hidden ${isRecommended ? 'border-emerald-500/50 bg-emerald-500/5' : 'bg-zinc-900/50 border-zinc-800 hover:border-blue-500'
                                }`}
                        >
                            {isRecommended && (
                                <div className="absolute top-0 right-0 bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg">
                                    ⭐ ÖNERİLEN
                                </div>
                            )}
                            <CardHeader className="pb-3">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <Cpu className={`w-5 h-5 ${isRecommended ? 'text-emerald-400' : 'text-zinc-400'}`} />
                                            {node.gpu_model}
                                            <div className="ml-2 inline-flex items-center border border-emerald-600 bg-emerald-950/50 rounded-full px-2 py-0.5 text-xs font-semibold text-emerald-300">
                                                Skor: {node.score?.toFixed(1)}
                                            </div>
                                        </CardTitle>
                                        <CardDescription className="flex items-center gap-3 text-xs mt-1">
                                            <span className="text-zinc-400">
                                                ✅ <strong className="text-white">{node.idle_nodes}</strong> / {node.total_nodes} Müsait
                                            </span>
                                            <span className="text-zinc-600">•</span>
                                            <span className={`font-mono ${node.reliability > 98 ? 'text-emerald-400' : 'text-yellow-400'}`}>
                                                Güvenilirlik: {node.reliability}%
                                            </span>
                                        </CardDescription>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-zinc-400">Saatlik Ücret</div>
                                        <div className="text-2xl font-bold text-emerald-400 flex items-center">
                                            <DollarSign className="w-5 h-5 text-zinc-500" />
                                            {node.price_hourly}
                                        </div>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {/* Quick Stats */}
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                    <div className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                                        <HardDrive className="w-4 h-4 text-purple-400" />
                                        <div>
                                            <div className="text-zinc-500">VRAM</div>
                                            <div className="font-mono text-white">24GB</div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                                        <Zap className="w-4 h-4 text-yellow-400" />
                                        <div>
                                            <div className="text-zinc-500">CUDA</div>
                                            <div className="font-mono text-white">12.1</div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                                        <Gauge className="w-4 h-4 text-blue-400" />
                                        <div>
                                            <div className="text-zinc-500">Performance</div>
                                            <div className="font-mono text-white">High</div>
                                        </div>
                                    </div>
                                </div>

                                {/* Expandable Details */}
                                <button
                                    onClick={() => setShowDetails(isExpanded ? null : i)}
                                    className="w-full flex items-center justify-between p-2 bg-zinc-800/30 hover:bg-zinc-800/50 rounded text-sm transition"
                                >
                                    <span className="text-zinc-400">Detaylı Bilgi & Maliyet Tahmini</span>
                                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                </button>

                                {isExpanded && (
                                    <div className="p-3 bg-zinc-900/80 rounded border border-zinc-800 space-y-3 animate-in fade-in slide-in-from-top-2">
                                        <div className="space-y-2 text-xs">
                                            <h5 className="font-semibold text-zinc-200">📈 Maliyet Analizi</h5>
                                            <div className="grid grid-cols-2 gap-2">
                                                <div className="flex justify-between">
                                                    <span className="text-zinc-500">1 Saat:</span>
                                                    <span className="text-white font-mono">${node.price_hourly}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-zinc-500">1 Gün (24sa):</span>
                                                    <span className="text-white font-mono">${(node.price_hourly * 24).toFixed(2)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-zinc-500">1 Hafta:</span>
                                                    <span className="text-white font-mono">${(node.price_hourly * 24 * 7).toFixed(2)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-zinc-500">1 Ay (30g):</span>
                                                    <span className="text-white font-mono">${(node.price_hourly * 24 * 30).toFixed(2)}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {isRecommended && (
                                            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded">
                                                <h5 className="font-semibold text-emerald-300 text-xs mb-1">✨ Neden Öneriliyor?</h5>
                                                <p className="text-[11px] text-emerald-200/80">
                                                    Bu GPU, kodunuzun gereksinimlerini karşılıyor, yüksek güvenilirliğe sahip ve
                                                    fiyat/performans oranı en iyi seçenek. {node.idle_nodes} adet müsait node mevcut.
                                                </p>
                                            </div>
                                        )}

                                        <div className="text-xs space-y-1 text-zinc-400">
                                            <div className="flex items-center gap-2">
                                                <Check className="w-3 h-3 text-emerald-500" />
                                                <span>Anlık kullanılabilir durumda</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Check className="w-3 h-3 text-emerald-500" />
                                                <span>Otomatik ortam kurulumu</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Check className="w-3 h-3 text-emerald-500" />
                                                <span>İstediğiniz zaman iptal edebilirsiniz</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Action Button */}
                                <Button
                                    className={`w-full ${isRecommended ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-blue-600 hover:bg-blue-500'}`}
                                    onClick={() => onSelect(node)}
                                >
                                    Bu GPU'yu Seç & Devam Et
                                    <ChevronRight className="w-4 h-4 ml-2" />
                                </Button>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>

            {recommendedNodes.length === 0 && (
                <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 border-2 border-dashed border-zinc-800 rounded-lg bg-zinc-900/20 m-4 p-8">
                    <Server className="w-12 h-12 mb-4 opacity-20" />
                    <p className="text-center">Uygun GPU bulunamadı.<br />Lütfen analiz parametrelerini gözden geçirin.</p>
                </div>
            )}
        </div>
    )
}
