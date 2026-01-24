export interface SshConfig {
    hostname: string;
    port: number;
    username: string;
    privateKey?: string;
    authType: 'key' | 'password';
    password?: string;
    passphrase?: string;
}

export interface UploadedFile {
    filename: string;
    local_path: string;
    size: number;
    type: 'script' | 'requirements' | 'config' | 'data' | 'other';
    isProject?: boolean;
    file_count?: number;
    entry_point?: string;
}

export interface ExecutionReport {
    jobId: string;
    gpu: string;
    startTime: string;
    endTime: string;
    durationSeconds: number;
    totalCost: number;
    exitCode: number;
    logsCount: number;
    status: 'success' | 'failed' | 'cancelled';
}

export interface CostEstimate {
    pricePerHour: number;
    elapsedSeconds: number;
    currentCost: number;
    projectedHourlyCost: number;
}

export interface WizardSession {
    currentStep: number;
    selectedGpu?: any;
    fileInfo?: UploadedFile;
    sshConfig?: SshConfig;
    analysisResult?: any;
    lastUpdated?: number;
}
