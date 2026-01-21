"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, Server, Zap, AlertTriangle } from "lucide-react"
import { useEffect, useState } from "react"

// Mock Data Type
interface MarketStatus {
  source: string
  node_count: number
  sample: any[]
}

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function DashboardPage() {
  const [status, setStatus] = useState<MarketStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/market/status`)
        if (res.ok) {
          const data = await res.json()
          setStatus(data)
        }
      } catch (error) {
        console.error("Failed to fetch market data", error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  return (
    <div className="p-8 space-y-8">
      <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4</div>
            <p className="text-xs text-muted-foreground">Auditor, Sniper, Architect, Executor</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Market Nodes</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "..." : status?.node_count || "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">Available on io.net</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Zap className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">100%</div>
            <p className="text-xs text-muted-foreground">Operational</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">0</div>
            <p className="text-xs text-muted-foreground">No critical issues</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions / Recent Activity could go here */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 max-h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle>Market Snapshot (Live via io.net)</CardTitle>
          </CardHeader>
          <CardContent className="pl-2 pr-2 overflow-y-auto flex-1">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-10 space-y-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
                <p className="text-sm text-muted-foreground">Fetching best nodes...</p>
              </div>
            ) : (
              <div className="space-y-3 px-2">
                {status?.sample?.map((node: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-4 border border-zinc-800 rounded-lg bg-zinc-950/50 hover:bg-zinc-900 transition-colors group">

                    {/* Left: Model & ID */}
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 font-bold text-xs ring-1 ring-emerald-500/20">
                        {(node.score || 0).toFixed(1)}
                      </div>
                      <div className="space-y-1">
                        <p className="font-semibold text-zinc-200">{node.gpu_model}</p>
                        <div className="flex items-center gap-2 text-xs text-zinc-500">
                          <span className="font-mono bg-zinc-900 px-1 rounded text-[10px]">{node.id}</span>
                          <span>•</span>
                          <span>Reliability: {node.reliability}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Middle: Stats */}
                    <div className="hidden md:flex items-center gap-6">
                      <div className="text-right">
                        <p className="text-xs text-zinc-400">Availability</p>
                        <div className={`space-x-1 font-mono font-medium ${node.idle_nodes > 0 ? "text-emerald-400" : "text-red-400"}`}>
                          <span>{node.idle_nodes}</span>
                          <span className="text-zinc-600">/</span>
                          <span className="text-zinc-500">{node.total_nodes}</span>
                          <span className="text-[10px] ml-1 text-zinc-600">IDLE</span>
                        </div>
                      </div>

                      <div className="text-right">
                        <p className="text-xs text-zinc-400">Active Rentals</p>
                        <p className="font-mono text-zinc-300">{node.hired_nodes}</p>
                      </div>
                    </div>

                    {/* Right: Price */}
                    <div className="text-right pl-4 border-l border-zinc-800 min-w-[100px]">
                      <div className="text-sm text-zinc-400">Hourly Rate</div>
                      <div className="text-lg font-bold text-emerald-400">
                        ${node.price_hourly}
                      </div>
                    </div>

                  </div>
                ))}

                {(!status?.sample || status.sample.length === 0) && (
                  <div className="text-center py-10 text-zinc-500">
                    <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-20" />
                    <p>No market data available.</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
