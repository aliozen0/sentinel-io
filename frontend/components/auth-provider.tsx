"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const router = useRouter()
    const pathname = usePathname()
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
    }, [])

    useEffect(() => {
        if (!mounted) return

        const token = localStorage.getItem("token")
        const isLoginPage = pathname === "/login"

        if (!token && !isLoginPage) {
            router.push("/login")
        }

        if (token && isLoginPage) {
            router.push("/")
        }

    }, [mounted, pathname, router])

    if (!mounted) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-zinc-950">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
            </div>
        )
    }

    return <>{children}</>
}
