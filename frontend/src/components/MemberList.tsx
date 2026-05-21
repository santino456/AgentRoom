import type { Member, AgentStatus } from '../types'

interface MemberListProps {
  members: Member[]
  agentStatus: Record<string, AgentStatus>
  showMembers: boolean
}

export default function MemberList({ members, agentStatus, showMembers }: MemberListProps) {
  return (
    <aside
      className={`fixed lg:static inset-y-0 right-0 z-50 w-52 flex-shrink-0 flex flex-col transition-transform duration-300 lg:translate-x-0 ${
        showMembers ? 'translate-x-0' : 'translate-x-full'
      }`}
      style={{ borderRadius: '24px 0 0 24px', backgroundColor: 'var(--bg-elevated)' }}
    >
      <div className="p-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
        Members — {members.length}
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {members.map((m) => {
          const status = agentStatus[m.name]
          let statusColor = 'bg-[var(--status-offline)]'
          let statusText = 'Offline'
          if (status) {
            if (status.process_online && status.listening) {
              statusColor = 'bg-[#00d4aa]'
              statusText = 'Online'
            } else if (status.process_online) {
              statusColor = 'bg-yellow-400'
              statusText = 'Process'
            }
          }
          return (
            <div key={m.id} className="flex items-center gap-2 px-2 py-1.5 rounded-2xl transition-colors hover:bg-white/[0.05]">
              <div className={`w-2 h-2 rounded-full ${statusColor}`} title={statusText} />
              <div className="flex flex-col min-w-0">
                <span className="text-sm truncate">{m.name}</span>
                {status && (
                  <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                    {status.process_online ? (status.listening ? 'Listening' : 'Not listening') : 'Offline'}
                  </span>
                )}
              </div>
              <span className="text-[10px] ml-auto" style={{ color: 'var(--text-muted)' }}>
                {m.type}
              </span>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
