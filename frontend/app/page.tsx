"use client"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Activity, Server, Zap, AlertTriangle, Info, TrendingDown, DollarSign } from "lucide-react"
import { useEffect, useState } from "react"

// Types matching backend response
interface Financials {
  balance: number
  currency: string
  hourly_burn: number
  rewards_24h: number
}

interface DashboardStats {
  active_agents: number
  market_nodes: number
  market_sample: any[]
  system_health: number
  alerts_count: number
  financials: Financials
}

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("token")
        if (!token) return // AuthProvider will handle redirect

        const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/dashboard/stats`, {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        })

        if (res.status === 401) {
          localStorage.removeItem("token")
          window.location.href = "/login"
          return
        }

        if (res.ok) {
          const data = await res.json()
          setStats(data)
        }
      } catch (error) {
        console.error("Failed to fetch dashboard stats", error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  return (
    <div className="p-8 space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Mission Control</h2>
          <p className="text-muted-foreground mt-1">Real-time system telemetry and market intelligence.</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">

        {/* 1. Active Agents */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Activity className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {loading ? "..." : stats?.active_agents || 0}
            </div>
            <p className="text-xs text-muted-foreground">Auditor, Sniper, Architect, Executor</p>
          </CardContent>
        </Card>

        {/* 2. Global Compute Market */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Global GPU Nodes</CardTitle>
            <Server className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {loading ? "..." : stats?.market_nodes.toLocaleString() || "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">Discoverable via io.net Explorer</p>
          </CardContent>
        </Card>

        {/* 3. System Health */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Zap className={`h-4 w-4 ${stats?.system_health === 100 ? "text-emerald-500" : "text-yellow-500"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold font-mono ${stats?.system_health === 100 ? "text-emerald-500" : "text-yellow-500"}`}>
              {loading ? "..." : `${stats?.system_health}%`}
            </div>
            <p className="text-xs text-muted-foreground">{stats?.alerts_count === 0 ? "All Systems Operational" : `${stats?.alerts_count} Active Alerts`}</p>
          </CardContent>
        </Card>

        {/* 4. Financial Status (Real Balance) */}
        <Card className="border-emerald-500/20 bg-emerald-500/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-emerald-400">Available Credits</CardTitle>
            <DollarSign className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold font-mono text-emerald-400">
                {loading ? "..." : `$${stats?.financials.balance.toFixed(2)}`}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Layout */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">

        {/* Market Snapshot Table */}
        <Card className="col-span-4 max-h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle>Market Intelligence Snapshot (Top 20 Nodes)</CardTitle>
            <CardDescription className="flex items-center justify-between">
              <span>Live Top-Rated Nodes (Refreshes automatically)</span>
              <span className="text-[10px] font-mono bg-blue-500/10 text-blue-500 px-2 py-1 rounded border border-blue-500/20">
                DATA SOURCE: io.net Explorer API
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2 pr-2 overflow-y-auto flex-1 min-h-[500px]">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-10 space-y-3 h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
                <p className="text-sm text-muted-foreground">Syncing with io.net...</p>
              </div>
            ) : (
              <div className="space-y-3 px-2">
                {stats?.market_sample?.map((node: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-4 border border-zinc-800 rounded-lg bg-zinc-950/50 hover:bg-zinc-900 transition-colors group">

                    {/* Left: Model & ID */}
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 font-bold text-xs ring-1 ring-blue-500/20">
                        {(node.score || 0).toFixed(1)}
                      </div>
                      <div className="space-y-1">
                        <p className="font-semibold text-zinc-200">{node.gpu_model}</p>
                        <div className="flex items-center gap-2 text-xs text-zinc-500">
                          <span className="font-mono bg-zinc-900 px-1 rounded text-[10px]">{node.id.substring(0, 12)}</span>
                          <span>•</span>
                          <span className={`${node.reliability > 98 ? "text-emerald-500" : "text-zinc-500"}`}>{node.reliability}% Uptime</span>
                        </div>
                      </div>
                    </div>

                    {/* Middle: Stats */}
                    <div className="hidden md:flex items-center gap-6">
                      <div className="text-right">
                        <p className="text-xs text-zinc-400">Cluster Size</p>
                        <div className="font-mono font-medium text-zinc-300">
                          {node.total_nodes || 1} Nodes
                        </div>
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

                {(!stats?.market_sample || stats.market_sample.length === 0) && (
                  <div className="flex flex-col items-center justify-center h-full text-zinc-500">
                    <AlertTriangle className="h-8 w-8 mb-2 opacity-20" />
                    <p>No market data available.</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info Panel / Logs Preview (Placeholder for future) */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>System Notifications</CardTitle>
            <CardDescription>Recent Agent Activity & Alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats?.alerts_count === 0 ? (
                <div className="flex items-center gap-4 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <Info className="h-5 w-5 text-emerald-500" />
                  <div>
                    <p className="text-sm font-medium text-emerald-500">All Systems Nominal</p>
                    <p className="text-xs text-emerald-400/70">No active threats or performance anomalies detected.</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-4 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  <div>
                    <p className="text-sm font-medium text-yellow-500">Attention Required</p>
                    <p className="text-xs text-yellow-400/70">{stats?.alerts_count} system alerts triggered in the last hour.</p>
                  </div>
                </div>
              )}

              <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800">
                <p className="text-xs font-mono text-zinc-500 mb-2">LATEST BROADCAST</p>
                <p className="text-sm text-zinc-300 italic">"Security sweep completed. 4 Agent nodes active and monitoring network traffic."</p>
                <p className="text-[10px] text-zinc-600 mt-2 text-right">- Watchdog Agent, 2m ago</p>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  )
}
