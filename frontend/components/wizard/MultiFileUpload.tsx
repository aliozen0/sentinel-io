"use client"

// Multi-File Upload Component - Support for multiple file types

import { useState, useRef, DragEvent } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Upload, FileCode, FileText, FileArchive, X, CheckCircle2, Loader2, Info } from "lucide-react"
import { UploadedFile } from "@/lib/wizard-types"

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface MultiFileUploadProps {
    onFilesChange: (files: UploadedFile[]) => void
    disabled?: boolean
}

const FILE_CONFIG = {
    '.py': { icon: FileCode, color: 'text-blue-400', type: 'script' as const, label: 'Python Script' },
    '.txt': { icon: FileText, color: 'text-yellow-400', type: 'requirements' as const, label: 'Requirements' },
    '.yaml': { icon: FileText, color: 'text-purple-400', type: 'config' as const, label: 'Config' },
    '.yml': { icon: FileText, color: 'text-purple-400', type: 'config' as const, label: 'Config' },
    '.json': { icon: FileText, color: 'text-orange-400', type: 'config' as const, label: 'JSON Config' },
    '.zip': { icon: FileArchive, color: 'text-emerald-400', type: 'data' as const, label: 'Zip Archive' }
}

const ACCEPTED_EXTENSIONS = Object.keys(FILE_CONFIG).join(',')

export default function MultiFileUpload({ onFilesChange, disabled = false }: MultiFileUploadProps) {
    const [files, setFiles] = useState<UploadedFile[]>([])
    const [uploading, setUploading] = useState<string | null>(null)
    const [isDragging, setIsDragging] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const getFileConfig = (filename: string) => {
        const ext = Object.keys(FILE_CONFIG).find(e => filename.endsWith(e))
        return ext ? FILE_CONFIG[ext as keyof typeof FILE_CONFIG] : { icon: FileText, color: 'text-zinc-400', type: 'other' as const, label: 'Other' }
    }

    const handleFileSelect = async (selectedFiles: FileList | null) => {
        if (!selectedFiles) return

        for (let i = 0; i < Math.min(selectedFiles.length, 5); i++) {
            const file = selectedFiles[i]
            const config = getFileConfig(file.name)

            // Check if already uploaded
            if (files.some(f => f.filename === file.name)) continue

            setUploading(file.name)

            try {
                const formData = new FormData()
                formData.append('file', file)

                const res = await fetch(`${NEXT_PUBLIC_API_URL}/v1/upload`, {
                    method: 'POST',
                    body: formData
                })

                if (res.ok) {
                    const data = await res.json()
                    const uploadedFile: UploadedFile = {
                        filename: data.filename,
                        local_path: data.local_path,
                        size: data.size,
                        type: config.type
                    }

                    setFiles(prev => {
                        const newFiles = [...prev, uploadedFile]
                        onFilesChange(newFiles)
                        return newFiles
                    })
                }
            } catch (err) {
                console.error('Upload failed:', err)
            } finally {
                setUploading(null)
            }
        }
    }

    const removeFile = (filename: string) => {
        setFiles(prev => {
            const newFiles = prev.filter(f => f.filename !== filename)
            onFilesChange(newFiles)
            return newFiles
        })
    }

    const handleDragOver = (e: DragEvent) => { e.preventDefault(); setIsDragging(true) }
    const handleDragLeave = (e: DragEvent) => { e.preventDefault(); setIsDragging(false) }
    const handleDrop = (e: DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        handleFileSelect(e.dataTransfer.files)
    }

    const mainScript = files.find(f => f.type === 'script')

    return (
        <div className="space-y-3">
            {/* Info */}
            <div className="flex items-start gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded text-xs text-blue-300">
                <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                    <p><strong>Desteklenen dosyalar:</strong> .py, requirements.txt, .yaml, .yml, .json, .zip</p>
                    <p className="text-blue-400 mt-1">Ana script (.py) zorunludur. Diğer dosyalar opsiyoneldir.</p>
                </div>
            </div>

            {/* Drop Zone */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !disabled && fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${disabled ? 'opacity-50 cursor-not-allowed border-zinc-800' :
                        isDragging ? 'border-blue-500 bg-blue-500/10' :
                            'border-zinc-700 hover:border-zinc-500 bg-zinc-950'
                    }`}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept={ACCEPTED_EXTENSIONS}
                    onChange={(e) => handleFileSelect(e.target.files)}
                    className="hidden"
                    disabled={disabled}
                />
                <Upload className={`w-8 h-8 mx-auto mb-2 ${isDragging ? 'text-blue-400' : 'text-zinc-500'}`} />
                <p className="text-zinc-400 text-sm">Dosyaları sürükleyin veya tıklayarak seçin</p>
                <p className="text-[10px] text-zinc-600 mt-1">Max. 5 dosya</p>
            </div>

            {/* Uploaded Files */}
            {files.length > 0 && (
                <div className="space-y-2">
                    {files.map((file) => {
                        const config = getFileConfig(file.filename)
                        const Icon = config.icon
                        const isMain = file.type === 'script'

                        return (
                            <div
                                key={file.filename}
                                className={`flex items-center gap-3 p-3 rounded-lg border transition ${isMain ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-zinc-800/50 border-zinc-700'
                                    }`}
                            >
                                <Icon className={`w-5 h-5 ${config.color}`} />
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium text-sm text-white truncate">{file.filename}</span>
                                        {isMain && (
                                            <span className="text-[10px] bg-emerald-500 text-white px-1.5 py-0.5 rounded">ANA SCRIPT</span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                                        <span>{config.label}</span>
                                        <span>•</span>
                                        <span>{(file.size / 1024).toFixed(1)} KB</span>
                                    </div>
                                </div>
                                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                                <button
                                    onClick={(e) => { e.stopPropagation(); removeFile(file.filename); }}
                                    className="p-1 hover:bg-zinc-700 rounded"
                                >
                                    <X className="w-4 h-4 text-zinc-500" />
                                </button>
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Uploading Indicator */}
            {uploading && (
                <div className="flex items-center gap-2 p-2 bg-blue-500/10 rounded text-xs text-blue-300">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>{uploading} yükleniyor...</span>
                </div>
            )}

            {/* Status */}
            {!mainScript && files.length > 0 && (
                <div className="flex items-center gap-2 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-xs text-yellow-300">
                    ⚠️ En az bir Python script (.py) gereklidir
                </div>
            )}
        </div>
    )
}
