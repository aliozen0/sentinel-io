"use client"

// Cost Display Widget - Real-time cost tracking display

import { DollarSign, Clock, AlertTriangle } from "lucide-react"

interface CostDisplayProps {
    isTracking: boolean
    formattedTime: string
    formattedCost: string
    currentCost: number
    pricePerHour: number
    budgetLimit?: number
    budgetWarning: boolean
}

export default function CostDisplay({
    isTracking,
    formattedTime,
    formattedCost,
    currentCost,
    pricePerHour,
    budgetLimit,
    budgetWarning
}: CostDisplayProps) {
    const budgetPercentage = budgetLimit ? Math.min((currentCost / budgetLimit) * 100, 100) : 0

    return (
        <div className={`rounded-lg border p-4 ${budgetWarning
                ? 'bg-yellow-500/10 border-yellow-500/30'
                : 'bg-zinc-900/50 border-zinc-800'
            }`}>
            <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm flex items-center gap-2">
                    <DollarSign className={`w-4 h-4 ${budgetWarning ? 'text-yellow-400' : 'text-emerald-400'}`} />
                    Canlı Maliyet Takibi
                </h4>
                {isTracking && (
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-emerald-500/20 rounded text-[10px] text-emerald-400">
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                        CANLI
                    </div>
                )}
            </div>

            <div className="grid grid-cols-2 gap-4">
                {/* Timer */}
                <div className="text-center p-3 bg-zinc-950/50 rounded">
                    <div className="flex items-center justify-center gap-1 text-zinc-400 text-xs mb-1">
                        <Clock className="w-3 h-3" />
                        Geçen Süre
                    </div>
                    <div className="font-mono text-xl font-bold text-white">
                        {formattedTime}
                    </div>
                </div>

                {/* Current Cost */}
                <div className="text-center p-3 bg-zinc-950/50 rounded">
                    <div className="flex items-center justify-center gap-1 text-zinc-400 text-xs mb-1">
                        <DollarSign className="w-3 h-3" />
                        Anlık Maliyet
                    </div>
                    <div className={`font-mono text-xl font-bold ${budgetWarning ? 'text-yellow-400' : 'text-emerald-400'}`}>
                        {formattedCost}
                    </div>
                </div>
            </div>

            {/* Rate Info */}
            <div className="mt-3 text-center text-xs text-zinc-500">
                Ücret: ${pricePerHour}/saat
            </div>

            {/* Budget Progress */}
            {budgetLimit && (
                <div className="mt-3 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-zinc-400">Bütçe Kullanımı</span>
                        <span className={budgetWarning ? 'text-yellow-400' : 'text-zinc-300'}>
                            {formattedCost} / ${budgetLimit.toFixed(2)}
                        </span>
                    </div>
                    <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all ${budgetWarning ? 'bg-yellow-500' : 'bg-emerald-500'
                                }`}
                            style={{ width: `${budgetPercentage}%` }}
                        />
                    </div>
                    {budgetWarning && (
                        <div className="flex items-center gap-1 text-xs text-yellow-400 mt-1">
                            <AlertTriangle className="w-3 h-3" />
                            Bütçe limitine yaklaşıyorsunuz!
                        </div>
                    )}
                </div>
            )}

            {/* Projections */}
            <div className="mt-3 pt-3 border-t border-zinc-800 grid grid-cols-3 gap-2 text-xs">
                <div className="text-center">
                    <div className="text-zinc-500">1 Saat</div>
                    <div className="text-white font-mono">${pricePerHour.toFixed(2)}</div>
                </div>
                <div className="text-center">
                    <div className="text-zinc-500">1 Gün</div>
                    <div className="text-white font-mono">${(pricePerHour * 24).toFixed(2)}</div>
                </div>
                <div className="text-center">
                    <div className="text-zinc-500">1 Hafta</div>
                    <div className="text-white font-mono">${(pricePerHour * 24 * 7).toFixed(2)}</div>
                </div>
            </div>
        </div>
    )
}
