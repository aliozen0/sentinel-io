"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { KeyRound, Lock, Eye, EyeOff } from "lucide-react";

interface SshConnectionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave?: (config: any) => void;
    initialValues?: {
        hostname?: string;
        port?: number;
        username?: string;
        authType?: string;
        privateKey?: string;
        password?: string;
        passphrase?: string;
    };
}

export function SshConnectionModal({ isOpen, onClose, onSave, initialValues }: SshConnectionModalProps) {
    const [hostname, setHostname] = useState(initialValues?.hostname || "");
    const [port, setPort] = useState(initialValues?.port?.toString() || "22");
    const [username, setUsername] = useState(initialValues?.username || "root");
    const [authType, setAuthType] = useState<"key" | "password">(initialValues?.authType as any || "key");
    const [privateKey, setPrivateKey] = useState(initialValues?.privateKey || "");
    const [password, setPassword] = useState(initialValues?.password || "");
    const [passphrase, setPassphrase] = useState(initialValues?.passphrase || "");
    const [showPassword, setShowPassword] = useState(false);
    const [showPassphrase, setShowPassphrase] = useState(false);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

    // Update form when initialValues change (for auto-fill)
    useEffect(() => {
        if (initialValues) {
            setHostname(initialValues.hostname || "");
            setPort(initialValues.port?.toString() || "22");
            setUsername(initialValues.username || "root");
            setAuthType(initialValues.authType as any || "key");
            setPrivateKey(initialValues.privateKey || "");
            setPassword(initialValues.password || "");
            setPassphrase(initialValues.passphrase || "");
        }
    }, [initialValues]);

    if (!isOpen) return null;

    async function handleTestConnection() {
        setLoading(true);
        setResult(null);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

            const body: any = {
                hostname,
                username,
                port: parseInt(port),
                auth_type: authType,
            };

            if (authType === "key") {
                body.private_key = privateKey;
                if (passphrase) {
                    body.passphrase = passphrase;
                }
            } else {
                body.password = password;
            }

            const res = await fetch(`${apiUrl}/v1/connection/test`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
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
        const config: any = {
            hostname,
            port: parseInt(port),
            username,
            authType,
        };

        if (authType === "key") {
            config.privateKey = privateKey;
            config.passphrase = passphrase;
        } else {
            config.password = password;
        }

        onSave?.(config);
        onClose();
    };

    const canTest = hostname && username && (
        (authType === "key" && privateKey) ||
        (authType === "password" && password)
    );

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
                    <span className="text-emerald-500">⚡</span> SSH Connection
                </h2>

                <div className="space-y-4">
                    {/* Host & Port */}
                    <div className="grid grid-cols-3 gap-4">
                        <div className="col-span-2 space-y-2">
                            <label className="text-xs text-zinc-400 uppercase">Hostname / IP</label>
                            <Input
                                placeholder="192.168.1.1 or gpu.example.com"
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

                    {/* Username */}
                    <div className="space-y-2">
                        <label className="text-xs text-zinc-400 uppercase">Username</label>
                        <Input
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="bg-zinc-950 border-zinc-800"
                        />
                    </div>

                    {/* Auth Type Selection */}
                    <div className="space-y-2">
                        <label className="text-xs text-zinc-400 uppercase">Authentication Method</label>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={() => setAuthType("key")}
                                className={`p-3 rounded-lg border text-sm font-medium transition-all flex items-center justify-center gap-2 ${authType === "key"
                                        ? "border-emerald-500 bg-emerald-500/10 text-emerald-400"
                                        : "border-zinc-700 hover:border-zinc-600 text-zinc-400"
                                    }`}
                            >
                                <KeyRound className="w-4 h-4" />
                                SSH Key
                            </button>
                            <button
                                onClick={() => setAuthType("password")}
                                className={`p-3 rounded-lg border text-sm font-medium transition-all flex items-center justify-center gap-2 ${authType === "password"
                                        ? "border-blue-500 bg-blue-500/10 text-blue-400"
                                        : "border-zinc-700 hover:border-zinc-600 text-zinc-400"
                                    }`}
                            >
                                <Lock className="w-4 h-4" />
                                Password
                            </button>
                        </div>
                    </div>

                    {/* SSH Key Auth */}
                    {authType === "key" && (
                        <>
                            <div className="space-y-2">
                                <label className="text-xs text-zinc-400 uppercase flex justify-between">
                                    <span>Private Key (PEM)</span>
                                    <span className="text-zinc-600 text-[10px]">RSA, Ed25519, ECDSA</span>
                                </label>
                                <Textarea
                                    placeholder="-----BEGIN RSA PRIVATE KEY-----..."
                                    value={privateKey}
                                    onChange={(e) => setPrivateKey(e.target.value)}
                                    className="bg-zinc-950 border-zinc-800 font-mono text-xs h-28"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs text-zinc-400 uppercase flex justify-between">
                                    <span>Passphrase</span>
                                    <span className="text-zinc-600 text-[10px]">Optional - for encrypted keys</span>
                                </label>
                                <div className="relative">
                                    <Input
                                        type={showPassphrase ? "text" : "password"}
                                        placeholder="Leave empty if key is not encrypted"
                                        value={passphrase}
                                        onChange={(e) => setPassphrase(e.target.value)}
                                        className="bg-zinc-950 border-zinc-800 pr-10"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassphrase(!showPassphrase)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                                    >
                                        {showPassphrase ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>
                        </>
                    )}

                    {/* Password Auth */}
                    {authType === "password" && (
                        <div className="space-y-2">
                            <label className="text-xs text-zinc-400 uppercase">Password</label>
                            <div className="relative">
                                <Input
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Enter your SSH password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="bg-zinc-950 border-zinc-800 pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Result */}
                    {result && (
                        <div className={`p-3 rounded text-sm ${result.success ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>
                            <strong className="block mb-1">{result.success ? "Connection Established!" : "Connection Failed"}</strong>
                            {result.message}
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex justify-end gap-3 pt-4">
                        <Button variant="ghost" onClick={onClose} className="text-zinc-400 hover:text-white">
                            Cancel
                        </Button>
                        <Button
                            onClick={handleTestConnection}
                            disabled={loading || !canTest}
                            className="bg-blue-600 hover:bg-blue-500 text-white min-w-[120px]"
                        >
                            {loading ? "Testing..." : "Test Connection"}
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
