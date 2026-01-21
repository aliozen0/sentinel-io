"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { CheckCircle2, AlertTriangle, XCircle, Search } from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function AnalyzePage() {
    const [code, setCode] = useState("import torch\nimport torch.nn as nn\n\n# Paste your training code here...")
    const [budget, setBudget] = useState(10.0)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)

    const handleAnalyze = async () => {
        setLoading(true)
        setResult(null)
        try {
            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, budget })
            })
            if (res.ok) {
                const data = await res.json()
                setResult(data)
            }
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="p-8 space-y-8 h-full flex flex-col">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold tracking-tight">Code Audit & Planning</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
                {/* Input Column */}
                <div className="space-y-4 flex flex-col">
                    <Card className="flex-1 flex flex-col">
                        <CardHeader>
                            <CardTitle>Source Code</CardTitle>
                            <CardDescription>Paste your training script for static analysis.</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1 flex flex-col space-y-4">
                            <Textarea
                                className="font-mono text-sm flex-1 min-h-[400px]"
                                value={code}
                                onChange={(e) => setCode(e.target.value)}
                            />
                            <div className="flex items-center gap-4">
                                <div className="flex-1">
                                    <span className="text-sm font-medium mb-1 block">Hourly Budget ($)</span>
                                    <Input
                                        type="number"
                                        value={budget}
                                        onChange={(e) => setBudget(parseFloat(e.target.value))}
                                    />
                                </div>
                                <Button className="mt-6" onClick={handleAnalyze} disabled={loading}>
                                    {loading ? "Analyzing..." : "Run Audit"}
                                    <Search className="ml-2 h-4 w-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Output Column */}
                <div className="space-y-4">
                    {result ? (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            {/* Auditor Report */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center">
                                        Auditor Report
                                        {result.audit.health_score > 80 ? (
                                            <CheckCircle2 className="ml-2 text-emerald-500 h-5 w-5" />
                                        ) : (
                                            <AlertTriangle className="ml-2 text-yellow-500 h-5 w-5" />
                                        )}
                                        <span className="ml-auto text-sm font-normal text-muted-foreground">Score: {result.audit.health_score}/100</span>
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 bg-muted rounded-md text-center">
                                            <div className="text-xs text-muted-foreground uppercase">Framework</div>
                                            <div className="font-bold">{result.audit.framework}</div>
                                        </div>
                                        <div className="p-3 bg-muted rounded-md text-center">
                                            <div className="text-xs text-muted-foreground uppercase">Min VRAM</div>
                                            <div className="font-bold">{result.audit.vram_min_gb} GB</div>
                                        </div>
                                    </div>

                                    {result.audit.critical_issues.length > 0 && (
                                        <div className="bg-destructive/10 p-4 rounded-md border border-destructive/20">
                                            <h4 className="text-destructive font-semibold mb-2 flex items-center">
                                                <XCircle className="h-4 w-4 mr-2" /> Critical Issues
                                            </h4>
                                            <ul className="list-disc list-inside text-sm space-y-1">
                                                {result.audit.critical_issues.map((issue: string, i: number) => (
                                                    <li key={i}>{issue}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Architect Plan */}
                            <Card>
                                <CardHeader><CardTitle>Environment Plan (The Architect)</CardTitle></CardHeader>
                                <CardContent>
                                    <div className="text-sm font-mono bg-black/50 p-4 rounded border">
                                        FROM {result.environment.image}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Sniper Recommendations */}
                            <Card>
                                <CardHeader><CardTitle>Market Opportunities (The Sniper)</CardTitle></CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        {result.market_recommendations.map((node: any, i: number) => (
                                            <div key={i} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition">
                                                <div>
                                                    <div className="font-bold">{node.id}</div>
                                                    <div className="text-xs text-muted-foreground">{node.gpu_model} • Rel: {node.reliability}%</div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-emerald-500 font-bold">${node.price_hourly}/hr</div>
                                                    <div className="text-xs text-muted-foreground">Score: {node.score.toFixed(2)}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    ) : (
                        <div className="h-full flex items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg">
                            Run an analysis to see the report.
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
