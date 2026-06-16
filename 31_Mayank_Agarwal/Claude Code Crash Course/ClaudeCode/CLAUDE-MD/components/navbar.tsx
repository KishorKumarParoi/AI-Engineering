'use client'

import { useTheme } from '@/lib/theme-provider'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

export function Navbar() {
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme } = useTheme()
  const router = useRouter()

  useEffect(() => {
    setMounted(true)
  }, [])

  const themeLabels: Record<string, string> = {
    light: 'Light',
    dark: 'Dark',
    system: 'System',
  }

  const nextTheme: Record<string, any> = {
    light: 'dark',
    dark: 'system',
    system: 'light',
  }

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
    router.refresh()
  }

  return (
    <nav className="sticky top-0 z-40 border-b border-gray-200 dark:border-slate-700 bg-gradient-to-r from-white to-slate-50 dark:from-slate-900 dark:to-slate-800 px-6 py-4 shadow-sm backdrop-blur-sm bg-white/95 dark:bg-slate-900/95">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            📋 Mayank's Job Tracker
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setTheme(nextTheme[theme] || 'light')}
            className="inline-flex items-center justify-center rounded-full p-2 text-sm font-medium text-gray-500 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
            title={`Switch to ${themeLabels[nextTheme[theme] || 'light']} mode`}
            aria-label={`Current theme: ${themeLabels[theme]}`}
          >
            {theme === 'light' && <span className="text-lg">🌙</span>}
            {theme === 'dark' && <span className="text-lg">☀️</span>}
            {theme === 'system' && <span className="text-lg">🖥️</span>}
          </button>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-100 transition-colors"
          >
            Sign out
          </button>
          <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1 text-xs font-medium text-slate-600 dark:text-slate-400">
            v0.1.0
          </span>
        </div>
      </div>
    </nav>
  )
}
