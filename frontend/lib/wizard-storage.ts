import { WizardSession } from './wizard-types';

const STORAGE_KEY = 'io-guard-wizard-session';

export const saveWizardSession = (updates: Partial<WizardSession>) => {
    if (typeof window === 'undefined') return;
    try {
        const current = loadWizardSession() || {};
        const updated = { ...current, ...updates, lastUpdated: Date.now() };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
        console.error("Failed to save wizard session", e);
    }
};

export const loadWizardSession = (): WizardSession | null => {
    if (typeof window === 'undefined') return null;
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : null;
    } catch (error) {
        console.error('Failed to load wizard session:', error);
        return null;
    }
};

export const clearWizardSession = () => {
    if (typeof window === 'undefined') return;
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
        console.error("Failed to clear wizard session", e);
    }
};

export const hasActiveSession = (): boolean => {
    return !!loadWizardSession();
};

export const getSessionAge = (): string => {
    const session = loadWizardSession();
    if (!session?.lastUpdated) return '';

    const diff = Date.now() - session.lastUpdated;
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return 'Şimdi';
    if (minutes < 60) return `${minutes}dk önce`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}sa önce`;
    return `${Math.floor(hours / 24)}g önce`;
};
