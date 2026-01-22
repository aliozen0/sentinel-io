"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CheckCircle2, ChevronRight, LayoutDashboard } from "lucide-react"
import StepAnalysis from "@/components/wizard/StepAnalysis"
import StepGpuSelection from "@/components/wizard/StepGpuSelection"
import StepDeployment from "@/components/wizard/StepDeployment"
import StepExecution from "@/components/wizard/StepExecution"

export default function WizardPage() {
    const [currentStep, setCurrentStep] = useState(1)

    // Global Wizard State
    const [analysisCode, setAnalysisCode] = useState<string>("")
    const [analysisResult, setAnalysisResult] = useState<any>(null)
    const [selectedGpu, setSelectedGpu] = useState<any>(null)
    const [deploymentConfig, setDeploymentConfig] = useState<any>(null)
    const [jobId, setJobId] = useState<string | null>(null)

    const steps = [
        { id: 1, name: "Analysis", description: "Audit code & requirements" },
        { id: 2, name: "Selection", description: "Choose optimal GPU" },
        { id: 3, name: "Deploy", description: "Connect & Upload" },
        { id: 4, name: "Execute", description: "Run & Monitor" }
    ]

    const handleAnalysisComplete = (code: string, result: any) => {
        setAnalysisCode(code)
        setAnalysisResult(result)
        setCurrentStep(2)
    }

    const handleGpuSelect = (gpu: any) => {
        setSelectedGpu(gpu)
        setCurrentStep(3)
    }

    const handleDeploymentReady = (config: any) => {
        setDeploymentConfig(config)
        setCurrentStep(4)
    }

    return (
        <div className="h-full flex flex-col p-6 space-y-6 max-w-7xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Deployment Wizard</h1>
                    <p className="text-zinc-400">End-to-end flow from code analysis to remote execution</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => window.location.href = '/'}>
                        Exit Wizard
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
                            <div key={step.id} className="flex flex-col items-center bg-zinc-950 px-4">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${isCompleted ? "bg-emerald-500 border-emerald-500 text-white" :
                                        isCurrent ? "bg-zinc-900 border-blue-500 text-blue-500" :
                                            "bg-zinc-900 border-zinc-700 text-zinc-500"
                                    }`}>
                                    {isCompleted ? <CheckCircle2 className="w-6 h-6" /> : <span className="font-bold">{step.id}</span>}
                                </div>
                                <div className="mt-2 text-center">
                                    <div className={`text-sm font-medium ${isCurrent ? "text-white" : "text-zinc-500"}`}>{step.name}</div>
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
                    />
                )}
                {currentStep === 4 && (
                    <StepExecution
                        deploymentConfig={deploymentConfig}
                        onBack={() => setCurrentStep(3)}
                    />
                )}
            </div>
        </div>
    )
}
