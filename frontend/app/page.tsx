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
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Market Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            {loading ? (
              <p className="p-4 text-sm text-muted-foreground">Loading market feed...</p>
            ) : (
              <div className="space-y-4">
                {status?.sample?.map((node: any, i: number) => (
                  <div key={i} className="flex items-center p-4 border rounded-lg bg-card/50">
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none">{node.gpu_model}</p>
                      <p className="text-sm text-muted-foreground">{node.id}</p>
                    </div>
                    <div className="ml-auto font-medium">
                      ${node.price_hourly}/hr
                    </div>
                  </div>
                ))}
                {(!status?.sample || status.sample.length === 0) && (
                  <p className="p-4 text-sm text-muted-foreground">No data available.</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
