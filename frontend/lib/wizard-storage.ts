// Wizard Storage - sessionStorage operations for session persistence
// Uses sessionStorage so credentials are cleared when browser closes

import { WizardSession, WIZARD_STORAGE_KEY, WIZARD_VERSION } from './wizard-types'

export function saveWizardSession(session: Partial<WizardSession>): void {
    try {
        const existing = loadWizardSession()
        const updated: WizardSession = {
            ...getDefaultSession(),
            ...existing,
            ...session,
            lastUpdated: new Date().toISOString(),
            version: WIZARD_VERSION
        }
        // Use sessionStorage - clears when browser/tab closes (secure for SSH creds)
        sessionStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify(updated))
    } catch (error) {
        console.error('Failed to save wizard session:', error)
    }
}

export function loadWizardSession(): WizardSession | null {
    try {
        const stored = sessionStorage.getItem(WIZARD_STORAGE_KEY)
        if (!stored) return null

        const session: WizardSession = JSON.parse(stored)

        // Version check - clear if outdated
        if (session.version !== WIZARD_VERSION) {
            clearWizardSession()
            return null
        }

        return session
    } catch (error) {
        console.error('Failed to load wizard session:', error)
        return null
    }
}

export function clearWizardSession(): void {
    try {
        sessionStorage.removeItem(WIZARD_STORAGE_KEY)
    } catch (error) {
        console.error('Failed to clear wizard session:', error)
    }
}

export function hasActiveSession(): boolean {
    const session = loadWizardSession()
    if (!session) return false

    // Session is valid as long as it exists (sessionStorage auto-clears on browser close)
    return session.step > 1
}

export function getSessionAge(): string {
    const session = loadWizardSession()
    if (!session) return ''

    const lastUpdated = new Date(session.lastUpdated)
    const now = new Date()
    const minutesDiff = Math.floor((now.getTime() - lastUpdated.getTime()) / (1000 * 60))

    if (minutesDiff < 1) return 'Az önce'
    if (minutesDiff < 60) return `${minutesDiff} dakika önce`

    const hoursDiff = Math.floor(minutesDiff / 60)
    return `${hoursDiff} saat önce`
}

function getDefaultSession(): WizardSession {
    return {
        step: 1,
        code: '',
        fileName: null,
        analysisResult: null,
        selectedGpu: null,
        deploymentConfig: null,
        sshConfig: null,
        connectionVerified: false,
        executionState: null,
        lastUpdated: new Date().toISOString(),
        version: WIZARD_VERSION
    }
}
