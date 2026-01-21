"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface SshConnectionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave?: (config: any) => void;
    initialValues?: {
        hostname?: string;
        port?: number;
        username?: string;
        privateKey?: string;
    };
}

export function SshConnectionModal({ isOpen, onClose, onSave, initialValues }: SshConnectionModalProps) {
    const [hostname, setHostname] = useState(initialValues?.hostname || "");
    const [port, setPort] = useState(initialValues?.port?.toString() || "22");
    const [username, setUsername] = useState(initialValues?.username || "root");
    const [privateKey, setPrivateKey] = useState(initialValues?.privateKey || "");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

    // Update form when initialValues change (for auto-fill)
    useEffect(() => {
        if (initialValues) {
            setHostname(initialValues.hostname || "");
            setPort(initialValues.port?.toString() || "22");
            setUsername(initialValues.username || "root");
            setPrivateKey(initialValues.privateKey || "");
        }
    }, [initialValues]);

    if (!isOpen) return null;

    async function handleTestConnection() {
        setLoading(true);
        setResult(null);

        try {
            // Use environment variable for API URL or fallback to localhost
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

            const res = await fetch(`${apiUrl}/v1/connection/test`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    hostname,
                    username,
                    private_key: privateKey,
                    port: parseInt(port),
                }),
            });

            const data = await res.json();
            setResult({
                success: data.success,
                message: data.message,
            });
        } catch (error) {
            setResult({
                success: false,
                message: "Failed to reach Backend API.",
            });
        } finally {
            setLoading(false);
        }
    }

    const handleSave = () => {
        const config = {
            hostname,
            port: parseInt(port),
            username,
            privateKey
        };
        onSave?.(config);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl p-6 relative">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-zinc-400 hover:text-white"
                >
                    ✕
                </button>

                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <span className="text-emerald-500">⚡</span> Establish Connection
                </h2>

                <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                        <div className="col-span-2 space-y-2">
                            <label className="text-xs text-zinc-400 uppercase">Hostname / IP</label>
                            <Input
                                placeholder="192.168.1.1"
                                value={hostname}
                                onChange={(e) => setHostname(e.target.value)}
                                className="bg-zinc-950 border-zinc-800 focus:ring-emerald-500/50"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs text-zinc-400 uppercase">Port</label>
                            <Input
                                value={port}
                                onChange={(e) => setPort(e.target.value)}
                                className="bg-zinc-950 border-zinc-800"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs text-zinc-400 uppercase">Username</label>
                        <Input
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="bg-zinc-950 border-zinc-800"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs text-zinc-400 uppercase flex justify-between">
                            <span>Private Key (PEM)</span>
                            <span className="text-zinc-600 text-[10px]">OpenSSH Format</span>
                        </label>
                        <Textarea
                            placeholder="-----BEGIN RSA PRIVATE KEY-----..."
                            value={privateKey}
                            onChange={(e) => setPrivateKey(e.target.value)}
                            className="bg-zinc-950 border-zinc-800 font-mono text-xs h-32"
                        />
                    </div>

                    {result && (
                        <div className={`p-3 rounded text-sm ${result.success ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>
                            <strong className="block mb-1">{result.success ? "Connection Established!" : "Connection Failed"}</strong>
                            {result.message}
                        </div>
                    )}

                    <div className="flex justify-end gap-3 pt-4">
                        <Button variant="ghost" onClick={onClose} className="text-zinc-400 hover:text-white">
                            Cancel
                        </Button>
                        <Button
                            onClick={handleTestConnection}
                            disabled={loading || !hostname || !privateKey}
                            className="bg-blue-600 hover:bg-blue-500 text-white min-w-[120px]"
                        >
                            {loading ? "Handshaking..." : "Test Connection"}
                        </Button>
                        {result?.success && onSave && (
                            <Button
                                onClick={handleSave}
                                className="bg-emerald-600 hover:bg-emerald-500 text-white min-w-[120px]"
                            >
                                ✓ Save & Close
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
