// useCostTracker - Real-time cost calculation hook

import { useState, useEffect, useCallback, useRef } from 'react'
import { CostEstimate } from '@/lib/wizard-types'

interface UseCostTrackerOptions {
    pricePerHour: number
    budgetLimit?: number
    onBudgetExceeded?: (cost: number) => void
}

interface UseCostTrackerReturn {
    isTracking: boolean
    elapsedSeconds: number
    currentCost: number
    formattedTime: string
    formattedCost: string
    budgetWarning: boolean
    startTracking: () => void
    stopTracking: () => void
    resetTracking: () => void
    getCostEstimate: () => CostEstimate
}

export function useCostTracker(options: UseCostTrackerOptions): UseCostTrackerReturn {
    const { pricePerHour, budgetLimit, onBudgetExceeded } = options

    const [isTracking, setIsTracking] = useState(false)
    const [elapsedSeconds, setElapsedSeconds] = useState(0)
    const [budgetWarning, setBudgetWarning] = useState(false)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)
    const startTimeRef = useRef<number | null>(null)
    const budgetExceededRef = useRef(false)

    // Calculate current cost
    const currentCost = (elapsedSeconds / 3600) * pricePerHour

    // Format time as HH:MM:SS
    const formattedTime = formatDuration(elapsedSeconds)

    // Format cost as $X.XXXX
    const formattedCost = `$${currentCost.toFixed(4)}`

    // Check budget
    useEffect(() => {
        if (budgetLimit && currentCost >= budgetLimit * 0.8) {
            setBudgetWarning(true)
        }
        if (budgetLimit && currentCost >= budgetLimit && !budgetExceededRef.current) {
            budgetExceededRef.current = true
            onBudgetExceeded?.(currentCost)
        }
    }, [currentCost, budgetLimit, onBudgetExceeded])

    const startTracking = useCallback(() => {
        if (isTracking) return

        setIsTracking(true)
        startTimeRef.current = Date.now()
        budgetExceededRef.current = false

        intervalRef.current = setInterval(() => {
            if (startTimeRef.current) {
                const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000)
                setElapsedSeconds(elapsed)
            }
        }, 1000)
    }, [isTracking])

    const stopTracking = useCallback(() => {
        setIsTracking(false)
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
        }
    }, [])

    const resetTracking = useCallback(() => {
        stopTracking()
        setElapsedSeconds(0)
        setBudgetWarning(false)
        startTimeRef.current = null
        budgetExceededRef.current = false
    }, [stopTracking])

    const getCostEstimate = useCallback((): CostEstimate => ({
        pricePerHour,
        elapsedSeconds,
        currentCost,
        projectedHourlyCost: pricePerHour
    }), [pricePerHour, elapsedSeconds, currentCost])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [])

    return {
        isTracking,
        elapsedSeconds,
        currentCost,
        formattedTime,
        formattedCost,
        budgetWarning,
        startTracking,
        stopTracking,
        resetTracking,
        getCostEstimate
    }
}

function formatDuration(seconds: number): string {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    return [hrs, mins, secs]
        .map(v => v.toString().padStart(2, '0'))
        .join(':')
}
