import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function riskColor(level: string): string {
  switch (level.toLowerCase()) {
    case 'critical': return 'text-red-400'
    case 'high': return 'text-orange-400'
    case 'medium': return 'text-yellow-400'
    case 'low': return 'text-green-400'
    default: return 'text-slate-400'
  }
}

export function riskBg(level: string): string {
  switch (level.toLowerCase()) {
    case 'critical': return 'bg-red-500/20 border-red-500/40'
    case 'high': return 'bg-orange-500/20 border-orange-500/40'
    case 'medium': return 'bg-yellow-500/20 border-yellow-500/40'
    case 'low': return 'bg-green-500/20 border-green-500/40'
    default: return 'bg-slate-500/20 border-slate-500/40'
  }
}

export function scoreColor(score: number): string {
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#f59e0b'
  if (score >= 40) return '#f97316'
  return '#ef4444'
}

export function confidenceLabel(conf: number): string {
  if (conf >= 0.8) return 'High'
  if (conf >= 0.5) return 'Medium'
  return 'Low'
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}
