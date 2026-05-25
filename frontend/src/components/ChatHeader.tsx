import { useState, useRef, useEffect } from 'react'
import type { ThemeName } from '../hooks/useTheme'
import { THEMES } from '../hooks/useTheme'

interface AgentStatus {
  process_online: boolean
  listening: boolean
  last_active: string
  type: string
}

interface ChatHeaderProps {
  roomName: string
  wsStatus: 'connecting' | 'open' | 'closed'
  theme: ThemeName
  onThemeChange: (theme: ThemeName) => void
  onToggleSidebar: () => void
  onToggleMembers: () => void
  agentStatus?: Record<string, AgentStatus>
  canGenerateInvite?: boolean
  onGenerateInvite?: () => void
}

// Get agent accent color
function getAgentColor(name: string): string {
  if (name.includes('claude')) return 'var(--accent-purple)'
  if (name.includes('kimi') || name.includes('Kimi')) return 'var(--accent-teal)'
  return 'var(--accent-blue)'
}

export default function ChatHeader({
  roomName,
  wsStatus,
  theme,
  onThemeChange,
  onToggleSidebar,
  onToggleMembers,
  agentStatus,
  canGenerateInvite,
  onGenerateInvite,
}: ChatHeaderProps) {
  const agents = agentStatus
    ? Object.entries(agentStatus).filter(([, status]) => status.type !== 'human')
    : []
  
  const [showThemeMenu, setShowThemeMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const currentTheme = THEMES.find(t => t.name === theme)

  // Close menu on outside click
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowThemeMenu(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  return (
    <header
      className="relative z-30 h-14 flex items-center px-3 lg:px-5 gap-3 nav-glass"
      style={{ 
        borderRadius: '0 0 20px 20px', 
        margin: '0 12px', 
        borderTop: 'none',
        borderBottom: '1px solid var(--border-color)',
      }}
    >
      <button
        onClick={onToggleSidebar}
        className="lg:hidden p-2 rounded-xl btn-press transition-all"
        style={{ color: 'var(--text-secondary)' }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
      
      <div className="flex items-center gap-2.5 flex-1 min-w-0">
        <div 
          className="w-8 h-8 rounded-xl flex items-center justify-center text-sm font-bold"
          style={{ 
            background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
            color: '#fff',
          }}
        >
          #
        </div>
        <div className="flex flex-col min-w-0">
          <span className="font-semibold text-sm truncate leading-tight">{roomName || 'Select Room'}</span>
          <div className="flex items-center gap-1">
            <span 
              className={`w-1.5 h-1.5 rounded-full ${wsStatus === 'open' ? 'status-pulse' : ''}`}
              style={{ 
                backgroundColor: wsStatus === 'open' 
                  ? 'var(--accent-green)' 
                  : wsStatus === 'connecting' 
                    ? 'var(--accent-amber)' 
                    : 'var(--accent-coral)',
              }}
            />
            <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
              {wsStatus === 'open' ? 'Connected' : wsStatus}
            </span>
          </div>
        </div>
      </div>

      {/* Agent status indicators */}
      {agents.length > 0 && (
        <div className="hidden md:flex items-center gap-2 mr-1">
          {agents.map(([name, status]) => {
            const color = getAgentColor(name)
            const isActive = status.process_online && status.listening
            return (
              <div
                key={name}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] transition-all"
                style={{
                  backgroundColor: isActive ? `${color}15` : 'var(--bg-surface)',
                  border: `1px solid ${isActive ? `${color}30` : 'var(--border-color)'}`,
                }}
                title={`${name}: ${status.process_online ? 'online' : 'offline'}${status.listening ? ', listening' : ''}`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${isActive ? 'status-pulse' : ''}`}
                  style={{
                    backgroundColor: isActive
                      ? color
                      : status.process_online
                        ? 'var(--accent-amber)'
                        : 'var(--accent-coral)',
                  }}
                />
                <span style={{ color: isActive ? color : 'var(--text-muted)' }}>
                  {name}
                </span>
              </div>
            )
          })}
        </div>
      )}

      <div className="flex items-center gap-1.5">
        {/* Invite link */}
        {canGenerateInvite && onGenerateInvite && (
          <button
            onClick={onGenerateInvite}
            className="p-2 rounded-xl transition-all btn-press hover:bg-white/5"
            style={{ color: 'var(--text-secondary)' }}
            title="Copy invite link"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
            </svg>
          </button>
        )}

        {/* Theme selector */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowThemeMenu(!showThemeMenu)}
            className="p-2 rounded-xl transition-all btn-press hover:bg-white/5 flex items-center gap-1"
            style={{ color: 'var(--text-secondary)' }}
            title="Change theme"
          >
            <span className="text-sm">{currentTheme?.icon}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform ${showThemeMenu ? 'rotate-180' : ''}`}>
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </button>
          
          {showThemeMenu && (
            <div 
              className="absolute right-0 top-full mt-2 py-1.5 rounded-xl dropdown-animate z-50 min-w-[160px]"
              style={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-color)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              }}
            >
              <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                Theme
              </div>
              {THEMES.map((t) => (
                <button
                  key={t.name}
                  onClick={() => { onThemeChange(t.name); setShowThemeMenu(false) }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm transition-all btn-press"
                  style={{
                    color: theme === t.name ? 'var(--accent-primary)' : 'var(--text-secondary)',
                    backgroundColor: theme === t.name ? 'var(--dark-surface-1)' : 'transparent',
                  }}
                >
                  <span className="text-base">{t.icon}</span>
                  <span className="flex-1 text-left">{t.label}</span>
                  {theme === t.name && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--accent-primary)' }}>
                      <path d="M20 6 9 17l-5-5"/>
                    </svg>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={onToggleMembers}
          className="lg:hidden p-2 rounded-xl transition-all btn-press hover:bg-white/5"
          style={{ color: 'var(--text-secondary)' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </button>
      </div>
    </header>
  )
}
