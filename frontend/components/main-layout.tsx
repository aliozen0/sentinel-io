"use client"

import { usePathname } from "next/navigation"
import { Sidebar } from "@/components/layout/sidebar"

export function MainLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname()
    const isLoginPage = pathname === "/login"

    if (isLoginPage) {
        return <main className="h-full">{children}</main>
    }

    return (
        <div className="h-full relative">
            <div className="hidden h-full md:flex md:w-72 md:flex-col md:fixed md:inset-y-0 z-[80] bg-gray-900 plugin-sidebar">
                <Sidebar />
            </div>
            <main className="md:pl-72 pb-10">
                {children}
            </main>
        </div>
    )
}
