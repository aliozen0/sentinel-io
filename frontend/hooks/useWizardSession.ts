// useWizardSession - React hook for wizard session management

import { useState, useEffect, useCallback } from 'react'
import { WizardSession } from '@/lib/wizard-types'
import {
    saveWizardSession,
    loadWizardSession,
    clearWizardSession,
    hasActiveSession,
    getSessionAge
} from '@/lib/wizard-storage'

interface UseWizardSessionReturn {
    session: WizardSession | null
    hasResumableSession: boolean
    sessionAge: string
    updateSession: (updates: Partial<WizardSession>) => void
    resumeSession: () => WizardSession | null
    clearSession: () => void
    dismissResume: () => void
}

export function useWizardSession(): UseWizardSessionReturn {
    const [session, setSession] = useState<WizardSession | null>(null)
    const [hasResumable, setHasResumable] = useState(false)
    const [sessionAge, setSessionAge] = useState('')
    const [dismissed, setDismissed] = useState(false)

    // Check for existing session on mount
    useEffect(() => {
        const hasSession = hasActiveSession()
        setHasResumable(hasSession && !dismissed)
        setSessionAge(getSessionAge())
    }, [dismissed])

    const updateSession = useCallback((updates: Partial<WizardSession>) => {
        saveWizardSession(updates)
        setSession(prev => prev ? { ...prev, ...updates } : null)
    }, [])

    const resumeSession = useCallback(() => {
        const loaded = loadWizardSession()
        if (loaded) {
            setSession(loaded)
            setHasResumable(false)
        }
        return loaded
    }, [])

    const clearSession = useCallback(() => {
        clearWizardSession()
        setSession(null)
        setHasResumable(false)
    }, [])

    const dismissResume = useCallback(() => {
        setDismissed(true)
        setHasResumable(false)
    }, [])

    return {
        session,
        hasResumableSession: hasResumable,
        sessionAge,
        updateSession,
        resumeSession,
        clearSession,
        dismissResume
    }
}
