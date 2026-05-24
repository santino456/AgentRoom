import { useState, useEffect, useCallback } from 'react'

export type ThemeName = 'midnight' | 'dawn' | 'ocean' | 'sunset' | 'forest' | 'cyber'

interface ThemeConfig {
  name: ThemeName
  label: string
  icon: string
  isDark: boolean
}

export const THEMES: ThemeConfig[] = [
  { name: 'midnight', label: 'Midnight', icon: '🌑', isDark: true },
  { name: 'dawn', label: 'Dawn', icon: '🌅', isDark: false },
  { name: 'ocean', label: 'Ocean', icon: '🌊', isDark: true },
  { name: 'sunset', label: 'Sunset', icon: '🌇', isDark: true },
  { name: 'forest', label: 'Forest', icon: '🌲', isDark: true },
  { name: 'cyber', label: 'Cyber', icon: '⚡', isDark: true },
]

export function useTheme() {
  const [theme, setTheme] = useState<ThemeName>(() => {
    const saved = localStorage.getItem('agentroom-theme') as ThemeName
    if (THEMES.find(t => t.name === saved)) return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'midnight' : 'dawn'
  })

  useEffect(() => {
    localStorage.setItem('agentroom-theme', theme)
  }, [theme])

  const setThemeName = useCallback((name: ThemeName) => {
    setTheme(name)
  }, [])

  const currentTheme = THEMES.find(t => t.name === theme) || THEMES[0]

  return { theme, setTheme: setThemeName, currentTheme }
}
