// Wizard Types - Shared type definitions for wizard features

export interface WizardSession {
    step: number
    code: string
    fileName: string | null
    analysisResult: any | null
    selectedGpu: any | null
    deploymentConfig: {
        sshConfig: any | null
        fileInfo: any | null
    } | null
    sshConfig: SshConfig | null
    connectionVerified: boolean
    fileInfo: any | null
    executionState: ExecutionState | null
    lastUpdated: string
    version: string
}

export interface ExecutionState {
    jobId: string | null
    startTime: string | null
    endTime: string | null
    logs: string[]
    status: 'idle' | 'running' | 'completed' | 'failed'
    exitCode: number | null
}

export interface CostEstimate {
    pricePerHour: number
    elapsedSeconds: number
    currentCost: number
    projectedHourlyCost: number
}

export interface UploadedFile {
    filename: string
    local_path: string
    size: number
    type: 'script' | 'requirements' | 'config' | 'data' | 'other'
}

export interface ExecutionReport {
    jobId: string
    gpu: string
    startTime: string
    endTime: string
    durationSeconds: number
    totalCost: number
    exitCode: number
    logsCount: number
    status: 'success' | 'failed' | 'timeout'
}

export interface GpuComparison {
    gpus: any[]
    recommendation: {
        bestValue: any
        bestPerformance: any
        aiRecommendation: string
    } | null
}

// Storage keys
export const WIZARD_STORAGE_KEY = 'io-guard-wizard-session'
export const WIZARD_VERSION = '1.1.0' // Bumped for new session format

// SSH Configuration Type
export interface SshConfig {
    hostname: string
    port: number
    username: string
    authType: 'key' | 'password'
    privateKey?: string
    password?: string
    passphrase?: string
}
