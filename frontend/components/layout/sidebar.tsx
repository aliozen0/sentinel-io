"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { LayoutDashboard, Code2, MessageSquare, Rocket, Settings, ShieldCheck, Workflow, User, LogOut, Brain } from "lucide-react"

const routes = [
    {
        label: "Dashboard",
        icon: LayoutDashboard,
        href: "/",
        color: "text-sky-500",
    },
    {
        label: "Deployment Wizard",
        icon: Workflow,
        href: "/wizard",
        color: "text-emerald-500",
    },
    {
        label: "Analyze Code",
        icon: Code2,
        href: "/analyze",
        color: "text-violet-500",
    },
    {
        label: "AI Chat",
        icon: MessageSquare,
        href: "/chat",
        color: "text-pink-700",
    },
    {
        label: "Knowledge",
        icon: Brain,
        href: "/knowledge",
        color: "text-purple-500",
    },
    {
        label: "Deploy",
        icon: Rocket,
        href: "/deploy",
        color: "text-orange-700",
    },
]

export function Sidebar() {
    const pathname = usePathname()

    const handleLogout = () => {
        localStorage.removeItem("token")
        window.location.href = "/login"
    }

    return (
        <div className="space-y-4 py-4 flex flex-col h-full bg-[#111827] text-white">
            <div className="px-3 py-2 flex-1">
                <Link href="/" className="flex items-center pl-3 mb-14">
                    <div className="relative w-8 h-8 mr-4">
                        <ShieldCheck className="h-8 w-8 text-emerald-500" />
                    </div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                        io-Guard
                    </h1>
                </Link>
                <div className="space-y-1">
                    {routes.map((route) => (
                        <Link
                            key={route.href}
                            href={route.href}
                            className={cn(
                                "text-sm group flex p-3 w-full justify-start font-medium cursor-pointer hover:text-white hover:bg-white/10 rounded-lg transition",
                                pathname === route.href ? "text-white bg-white/10" : "text-zinc-400"
                            )}
                        >
                            <div className="flex items-center flex-1">
                                <route.icon className={cn("h-5 w-5 mr-3", route.color)} />
                                {route.label}
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
            <div className="px-3 py-2 space-y-1">
                <Link
                    href="/account"
                    className={cn(
                        "text-sm group flex p-3 w-full justify-start font-medium cursor-pointer hover:text-white hover:bg-white/10 rounded-lg transition",
                        pathname === "/account" ? "text-white bg-white/10" : "text-zinc-400"
                    )}
                >
                    <User className="h-5 w-5 mr-3 text-gray-400" />
                    Account
                </Link>
                <div
                    onClick={handleLogout}
                    className="text-sm group flex p-3 w-full justify-start font-medium cursor-pointer hover:text-red-400 hover:bg-red-500/10 rounded-lg transition text-zinc-400"
                >
                    <LogOut className="h-5 w-5 mr-3" />
                    Logout
                </div>
            </div>
        </div>
    )
}
