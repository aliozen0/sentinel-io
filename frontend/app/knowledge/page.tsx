"use client"

import { useState, useCallback, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    Upload,
    FileText,
    Search,
    Trash2,
    Database,
    CheckCircle,
    XCircle,
    Loader2,
    Brain,
    File,
    AlertTriangle
} from "lucide-react"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Document {
    id: string
    source: string
    created_at: string
    metadata: Record<string, any>
}

interface SearchResult {
    content: string
    source: string
    score: number
    metadata: Record<string, any>
}

interface Stats {
    mode: string
    document_count: number
    storage: string
}

export default function KnowledgePage() {
    const [documents, setDocuments] = useState<Document[]>([])
    const [stats, setStats] = useState<Stats | null>(null)
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")
    const [searchResults, setSearchResults] = useState<SearchResult[]>([])
    const [searching, setSearching] = useState(false)
    const [dragActive, setDragActive] = useState(false)
    const [uploadMessage, setUploadMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    const getToken = () => localStorage.getItem("token")

    // Fetch documents and stats
    const fetchData = useCallback(async () => {
        try {
            const token = getToken()
            if (!token) return

            const [docsRes, statsRes] = await Promise.all([
                fetch(`${NEXT_PUBLIC_API_URL}/v1/knowledge/documents`, {
                    headers: { "Authorization": `Bearer ${token}` }
                }),
                fetch(`${NEXT_PUBLIC_API_URL}/v1/knowledge/stats`, {
                    headers: { "Authorization": `Bearer ${token}` }
                })
            ])

            if (docsRes.ok) {
                const docs = await docsRes.json()
                setDocuments(docs)
            }
            if (statsRes.ok) {
                const s = await statsRes.json()
                setStats(s)
            }
        } catch (error) {
            console.error("Failed to fetch knowledge data:", error)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    // Handle file upload
    const handleUpload = async (files: FileList | null) => {
        if (!files || files.length === 0) return

        const token = getToken()
        if (!token) {
            setUploadMessage({ type: 'error', text: 'Oturum açın' })
            return
        }

        setUploading(true)
        setUploadMessage(null)

        try {
            for (const file of Array.from(files)) {
                const formData = new FormData()
                formData.append('file', file)
                formData.append('chunk_size', '500')

                const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/knowledge/upload`, {
                    method: 'POST',
                    headers: { "Authorization": `Bearer ${token}` },
                    body: formData
                })

                const data = await res.json()

                if (res.ok && data.success) {
                    setUploadMessage({
                        type: 'success',
                        text: `✅ ${file.name}: ${data.chunks_added} chunk eklendi (${data.mode})`
                    })
                } else {
                    setUploadMessage({
                        type: 'error',
                        text: `❌ ${file.name}: ${data.detail || 'Yükleme başarısız'}`
                    })
                }
            }

            // Refresh data
            fetchData()
        } catch (error) {
            setUploadMessage({ type: 'error', text: `Hata: ${error}` })
        } finally {
            setUploading(false)
        }
    }

    // Handle search
    const handleSearch = async () => {
        if (!searchQuery.trim()) return

        const token = getToken()
        if (!token) return

        setSearching(true)

        try {
            const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/knowledge/search`, {
                method: 'POST',
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ query: searchQuery, top_k: 5 })
            })

            if (res.ok) {
                const results = await res.json()
                setSearchResults(results)
            }
        } catch (error) {
            console.error("Search failed:", error)
        } finally {
            setSearching(false)
        }
    }

    // Handle delete
    const handleDelete = async (docId: string) => {
        const token = getToken()
        if (!token) return

        try {
            await fetch(`${NEXT_PUBLIC_API_URL}/v1/knowledge/${docId}`, {
                method: 'DELETE',
                headers: { "Authorization": `Bearer ${token}` }
            })
            fetchData()
        } catch (error) {
            console.error("Delete failed:", error)
        }
    }

    // Drag and drop handlers
    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true)
        } else if (e.type === "dragleave") {
            setDragActive(false)
        }
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)
        handleUpload(e.dataTransfer.files)
    }

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                        <Brain className="h-8 w-8 text-purple-500" />
                        Bilgi Tabanı
                    </h2>
                    <p className="text-muted-foreground mt-1">
                        PDF ve TXT dosyaları yükleyerek AI'ı eğitin. RAG (Retrieval-Augmented Generation) ile akıllı arama yapın.
                    </p>
                </div>

                {/* Stats Badge */}
                {stats && (
                    <div className="flex items-center gap-2 px-4 py-2 bg-zinc-900 rounded-lg border border-zinc-800">
                        <Database className="h-4 w-4 text-emerald-500" />
                        <span className="text-sm font-mono">
                            {stats.document_count} doküman
                        </span>
                        <span className="text-xs text-zinc-500">
                            ({stats.mode})
                        </span>
                    </div>
                )}
            </div>

            {/* Render.com Warning */}
            <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <h3 className="font-semibold text-orange-200 mb-1">Render.com Altyapı Bilgilendirmesi</h3>
                        <p className="text-sm text-orange-200/80 leading-relaxed">
                            Render.com Free Plan kaynak kısıtlamaları (RAM/CPU) nedeniyle, büyük boyutlu dosya yüklemeleri ve işlemeleri başarısız olabilir veya çok uzun sürebilir.
                            Büyük projeleriniz için uygulamayı <a href="https://github.com/aliozen0/sentinel-io" target="_blank" rel="noopener noreferrer" className="text-orange-300 hover:underline">GitHub</a> üzerinden bilgisayarınıza indirip çalıştırmanız önerilir.
                        </p>
                    </div>
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid gap-6 lg:grid-cols-2">

                {/* Upload Section */}
                <Card className="lg:col-span-1">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Upload className="h-5 w-5 text-blue-500" />
                            Dosya Yükle
                        </CardTitle>
                        <CardDescription>
                            PDF veya TXT dosyalarını sürükleyip bırakın veya seçin
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {/* Drag & Drop Zone */}
                        <div
                            className={`
                relative border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer
                ${dragActive
                                    ? 'border-purple-500 bg-purple-500/10'
                                    : 'border-zinc-700 hover:border-zinc-500 hover:bg-zinc-900/50'}
              `}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                            onClick={() => document.getElementById('file-input')?.click()}
                        >
                            <input
                                id="file-input"
                                type="file"
                                accept=".pdf,.txt,.md,.json"
                                multiple
                                className="hidden"
                                onChange={(e) => handleUpload(e.target.files)}
                            />

                            {uploading ? (
                                <div className="flex flex-col items-center gap-3">
                                    <Loader2 className="h-10 w-10 text-purple-500 animate-spin" />
                                    <p className="text-sm text-zinc-400">Yükleniyor...</p>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center gap-3">
                                    <div className="h-16 w-16 rounded-full bg-purple-500/10 flex items-center justify-center">
                                        <FileText className="h-8 w-8 text-purple-500" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-zinc-200">Dosyaları buraya bırakın</p>
                                        <p className="text-sm text-zinc-500">veya seçmek için tıklayın</p>
                                    </div>
                                    <div className="flex gap-2 mt-2">
                                        <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400">.pdf</span>
                                        <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400">.txt</span>
                                        <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400">.md</span>
                                        <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400">.json</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Upload Message */}
                        {uploadMessage && (
                            <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 ${uploadMessage.type === 'success'
                                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                                : 'bg-red-500/10 border border-red-500/20 text-red-400'
                                }`}>
                                {uploadMessage.type === 'success'
                                    ? <CheckCircle className="h-4 w-4" />
                                    : <XCircle className="h-4 w-4" />
                                }
                                <span className="text-sm">{uploadMessage.text}</span>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Search Section */}
                <Card className="lg:col-span-1">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Search className="h-5 w-5 text-emerald-500" />
                            RAG Arama
                        </CardTitle>
                        <CardDescription>
                            Yüklenmiş dokümanlarda semantik arama yapın
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Search Input */}
                        <div className="flex gap-2">
                            <Input
                                placeholder="Arama sorgunuzu yazın..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                className="bg-zinc-900 border-zinc-700"
                            />
                            <Button
                                onClick={handleSearch}
                                disabled={searching || !searchQuery.trim()}
                                className="bg-emerald-600 hover:bg-emerald-700"
                            >
                                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                            </Button>
                        </div>

                        {/* Search Results */}
                        <div className="space-y-3 max-h-[300px] overflow-y-auto">
                            {searchResults.length === 0 && !searching && (
                                <p className="text-sm text-zinc-500 text-center py-8">
                                    Arama sonuçları burada görünecek
                                </p>
                            )}
                            {searchResults.map((result, i) => (
                                <div
                                    key={i}
                                    className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg space-y-2"
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-mono text-zinc-500">{result.source}</span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${result.score > 0.8 ? 'bg-emerald-500/20 text-emerald-400' :
                                            result.score > 0.5 ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-zinc-700 text-zinc-400'
                                            }`}>
                                            {(result.score * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <p className="text-sm text-zinc-300 line-clamp-3">{result.content}</p>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Documents List */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <File className="h-5 w-5 text-blue-500" />
                        Yüklenen Dokümanlar
                    </CardTitle>
                    <CardDescription>
                        Bilgi tabanındaki tüm dokümanlar
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-zinc-500" />
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="text-center py-12 text-zinc-500">
                            <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
                            <p>Henüz doküman yüklenmedi</p>
                            <p className="text-sm">Yukarıdaki alandan PDF veya TXT yükleyin</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {documents.map((doc) => (
                                <div
                                    key={doc.id}
                                    className="flex items-center justify-between p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg hover:bg-zinc-900 transition-colors"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                                            <FileText className="h-5 w-5 text-blue-500" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-zinc-200">{doc.source}</p>
                                            <p className="text-xs text-zinc-500">
                                                ID: {doc.id} • {new Date(doc.created_at).toLocaleString('tr-TR')}
                                            </p>
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleDelete(doc.id)}
                                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
