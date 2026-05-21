interface ChatHeaderProps {
  roomName: string
  wsStatus: 'connecting' | 'open' | 'closed'
  theme: 'dark' | 'light'
  onToggleTheme: () => void
  onToggleSidebar: () => void
  onToggleMembers: () => void
}

export default function ChatHeader({
  roomName,
  wsStatus,
  theme,
  onToggleTheme,
  onToggleSidebar,
  onToggleMembers,
}: ChatHeaderProps) {
  return (
    <header
      className="h-14 flex items-center px-3 lg:px-5 gap-2 liquid-glass"
      style={{ borderRadius: '0 0 20px 20px', margin: '0 12px', borderTop: 'none' }}
    >
      <button
        onClick={onToggleSidebar}
        className="lg:hidden p-2 rounded-lg hover:bg-[var(--bg-surface)]"
        style={{ color: 'var(--text-secondary)' }}
      >
        ☰
      </button>
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <span className="text-lg hidden sm:inline">#</span>
        <span className="font-semibold truncate">{roomName || 'Select Room'}</span>
      </div>
      <div className="flex items-center gap-2 text-xs">
        <button
          onClick={onToggleTheme}
          className="p-2 rounded-xl transition-all hover:bg-white/10 liquid-glass"
          title={theme === 'dark' ? 'Switch to light' : 'Switch to dark'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        <button
          onClick={onToggleMembers}
          className="lg:hidden p-2 rounded-xl hover:bg-white/10 transition-all liquid-glass"
        >
          👥
        </button>
        <span
          className={`w-2 h-2 rounded-full ${
            wsStatus === 'open'
              ? 'bg-[#00d4aa]'
              : wsStatus === 'connecting'
                ? 'bg-yellow-400'
                : 'bg-red-400'
          }`}
        />
        <span className="hidden sm:inline" style={{ color: 'var(--text-muted)' }}>
          {wsStatus === 'open' ? 'Live' : wsStatus}
        </span>
      </div>
    </header>
  )
}
