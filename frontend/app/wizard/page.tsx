"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { CheckCircle2, RotateCcw, X } from "lucide-react"
import StepAnalysis from "@/components/wizard/StepAnalysis"
import StepGpuSelection from "@/components/wizard/StepGpuSelection"
import StepDeployment from "@/components/wizard/StepDeployment"
import StepExecution from "@/components/wizard/StepExecution"
import { useWizardSession } from "@/hooks/useWizardSession"
import { saveWizardSession } from "@/lib/wizard-storage"
import { SshConfig } from "@/lib/wizard-types"

export default function WizardPage() {
    const [currentStep, setCurrentStep] = useState(1)

    // State for Wizard Step 1 (Analysis)
    const [analysisCode, setAnalysisCode] = useState<string>("")
    const [fileName, setFileName] = useState<string | null>(null)
    const [fileInfo, setFileInfo] = useState<any>(null) // Lifted file state for persistence
    const [analysisResult, setAnalysisResult] = useState<any>(null)
    const [selectedGpu, setSelectedGpu] = useState<any>(null)
    const [deploymentConfig, setDeploymentConfig] = useState<any>(null)

    // SSH State (lifted from StepDeployment for persistence)
    const [sshConfig, setSshConfig] = useState<SshConfig | null>(null)
    const [connectionVerified, setConnectionVerified] = useState(false)

    // Session persistence
    const { hasResumableSession, sessionAge, resumeSession, clearSession, dismissResume } = useWizardSession()
    const [showResumePrompt, setShowResumePrompt] = useState(false)

    // Check for resumable session on mount
    useEffect(() => {
        if (hasResumableSession) {
            setShowResumePrompt(true)
        }
    }, [hasResumableSession])

    // Save session on state changes
    useEffect(() => {
        if (currentStep > 1 || analysisCode || analysisResult) {
            saveWizardSession({
                step: currentStep,
                code: analysisCode,
                fileName,
                fileInfo, // Save file info
                analysisResult,
                selectedGpu,
                deploymentConfig,
                sshConfig,
                connectionVerified
            })
        }
    }, [currentStep, analysisCode, fileName, fileInfo, analysisResult, selectedGpu, deploymentConfig, sshConfig, connectionVerified])

    const handleResumeSession = () => {
        const session = resumeSession()
        if (session) {
            setCurrentStep(session.step)
            setAnalysisCode(session.code)
            setFileName(session.fileName)
            setFileInfo(session.fileInfo) // Restore file info
            setAnalysisResult(session.analysisResult)
            setSelectedGpu(session.selectedGpu)
            setDeploymentConfig(session.deploymentConfig)
            setSshConfig(session.sshConfig)
            setConnectionVerified(session.connectionVerified)
        }
        setShowResumePrompt(false)
    }

    const handleStartFresh = () => {
        clearSession()
        setShowResumePrompt(false)
    }

    const steps = [
        { id: 1, name: "Analiz", description: "Kod denetimi" },
        { id: 2, name: "GPU", description: "Seçim" },
        { id: 3, name: "Bağlantı", description: "Upload" },
        { id: 4, name: "Çalıştır", description: "İzle" }
    ]

    const handleAnalysisComplete = (code: string, result: any, fileInfoData?: any) => {
        setAnalysisCode(code)
        setAnalysisResult(result)
        if (fileInfoData) setFileInfo(fileInfoData)
        setCurrentStep(2)
    }

    const handleGpuSelect = (gpu: any) => {
        setSelectedGpu(gpu)
        setCurrentStep(3)
    }

    const handleDeploymentReady = (config: any) => {
        setDeploymentConfig(config)
        // If config includes fileInfo (from Step 3 upload), update it
        if (config.fileInfo) setFileInfo(config.fileInfo)

        setCurrentStep(4)
    }

    const handleRestart = () => {
        clearSession()
        setCurrentStep(1)
        setAnalysisCode("")
        setFileName(null)
        setFileInfo(null)
        setAnalysisResult(null)
        setSelectedGpu(null)
        setDeploymentConfig(null)
        setSshConfig(null)
        setConnectionVerified(false)
    }

    return (
        <div className="h-full flex flex-col p-6 space-y-6 max-w-7xl mx-auto w-full">
            {/* Resume Session Prompt */}
            {showResumePrompt && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 flex items-center justify-between animate-in slide-in-from-top-4">
                    <div className="flex items-center gap-3">
                        <RotateCcw className="w-5 h-5 text-blue-400" />
                        <div>
                            <p className="font-medium text-blue-200">Devam etmek ister misiniz?</p>
                            <p className="text-sm text-blue-300/70">
                                {sessionAge} kayıtlı bir oturum bulundu.
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={handleStartFresh}
                            className="border-blue-500/30 text-blue-300 hover:bg-blue-500/20"
                        >
                            <X className="w-4 h-4 mr-1" />
                            Yeniden Başla
                        </Button>
                        <Button
                            size="sm"
                            onClick={handleResumeSession}
                            className="bg-blue-600 hover:bg-blue-500"
                        >
                            <RotateCcw className="w-4 h-4 mr-1" />
                            Devam Et
                        </Button>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Deployment Wizard</h1>
                    <p className="text-zinc-400">Kodunuzu analiz edin, GPU seçin ve uzak sunucuda çalıştırın</p>
                </div>
                <div className="flex gap-2">
                    {currentStep > 1 && (
                        <Button variant="outline" onClick={handleRestart} size="sm">
                            <RotateCcw className="w-4 h-4 mr-2" />
                            Sıfırla
                        </Button>
                    )}
                    <Button variant="outline" onClick={() => window.location.href = '/'}>
                        Çıkış
                    </Button>
                </div>
            </div>

            {/* Stepper Indicator */}
            <div className="relative">
                <div className="absolute top-1/2 left-0 w-full h-0.5 bg-zinc-800 -z-10" />
                <div className="flex justify-between">
                    {steps.map((step) => {
                        const isCompleted = step.id < currentStep
                        const isCurrent = step.id === currentStep

                        return (
                            <div
                                key={step.id}
                                className="flex flex-col items-center bg-zinc-950 px-4 cursor-pointer"
                                onClick={() => {
                                    // Allow going back to completed steps
                                    if (isCompleted) setCurrentStep(step.id)
                                }}
                            >
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${isCompleted ? "bg-emerald-500 border-emerald-500 text-white" :
                                    isCurrent ? "bg-zinc-900 border-blue-500 text-blue-500" :
                                        "bg-zinc-900 border-zinc-700 text-zinc-500"
                                    }`}>
                                    {isCompleted ? <CheckCircle2 className="w-6 h-6" /> : <span className="font-bold">{step.id}</span>}
                                </div>
                                <div className="mt-2 text-center">
                                    <div className={`text-sm font-medium ${isCurrent ? "text-white" : isCompleted ? "text-emerald-400" : "text-zinc-500"}`}>
                                        {step.name}
                                    </div>
                                    <div className="text-xs text-zinc-600 hidden sm:block">{step.description}</div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 min-h-0 bg-zinc-900/30 border border-zinc-800 rounded-xl overflow-hidden shadow-xl">
                {currentStep === 1 && (
                    <StepAnalysis
                        onComplete={handleAnalysisComplete}
                        initialCode={analysisCode}
                        initialResult={analysisResult}
                        initialFileInfo={fileInfo} // Pass file info
                    />
                )}
                {currentStep === 2 && (
                    <StepGpuSelection
                        analysisResult={analysisResult}
                        onSelect={handleGpuSelect}
                        onBack={() => setCurrentStep(1)}
                    />
                )}
                {currentStep === 3 && (
                    <StepDeployment
                        selectedGpu={selectedGpu}
                        analysisResult={analysisResult}
                        onReady={handleDeploymentReady}
                        onBack={() => setCurrentStep(2)}
                        sshConfig={sshConfig}
                        setSshConfig={setSshConfig}
                        connectionVerified={connectionVerified}
                        setConnectionVerified={setConnectionVerified}
                        initialFileInfo={fileInfo}
                        setFileInfo={setFileInfo}
                    />
                )}
                {currentStep === 4 && (
                    <StepExecution
                        deploymentConfig={deploymentConfig}
                        selectedGpu={selectedGpu}
                        onBack={() => setCurrentStep(3)}
                        onRestart={handleRestart}
                    />
                )}
            </div>
        </div>
    )
}
