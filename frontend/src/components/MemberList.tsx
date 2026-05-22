import { useState } from 'react'
import type { Member, AgentStatus, MemberStats } from '../types'

interface MemberListProps {
  members: Member[]
  agentStatus: Record<string, AgentStatus>
  showMembers: boolean
  announcement: string
  memberStats: Record<number, MemberStats>
}

export default function MemberList({
  members,
  agentStatus,
  showMembers,
  announcement,
  memberStats,
}: MemberListProps) {
  const [selectedMember, setSelectedMember] = useState<Member | null>(null)

  const getStatus = (m: Member) => {
    const status = agentStatus[m.name]
    if (!status) return { color: 'bg-[var(--status-offline)]', text: 'Offline', label: 'Offline' }
    if (status.process_online && status.listening) {
      return { color: 'bg-[#00d4aa]', text: 'Online', label: 'Listening' }
    }
    if (status.process_online) {
      return { color: 'bg-yellow-400', text: 'Process', label: 'Not listening' }
    }
    return { color: 'bg-[var(--status-offline)]', text: 'Offline', label: 'Offline' }
  }

  const formatTime = (iso: string | null) => {
    if (!iso) return 'Never'
    try {
      const d = new Date(iso)
      const now = new Date()
      const isToday = d.toDateString() === now.toDateString()
      const pad = (n: number) => n.toString().padStart(2, '0')
      if (isToday) return `${pad(d.getHours())}:${pad(d.getMinutes())}`
      return `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch {
      return 'Never'
    }
  }

  return (
    <>
      <aside
        className={`fixed lg:static inset-y-0 right-0 z-50 w-64 flex-shrink-0 flex flex-col transition-transform duration-300 lg:translate-x-0 ${
          showMembers ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ borderRadius: '24px 0 0 24px', backgroundColor: 'var(--bg-elevated)' }}
      >
        {/* Announcement */}
        {announcement && (
          <div className="mx-3 mt-3 px-3 py-2.5 rounded-2xl liquid-glass">
            <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#00d4aa' }}>
              Announcement
            </div>
            <div className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>
              {announcement}
            </div>
          </div>
        )}

        <div className="p-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          Members — {members.length}
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {members.map((m) => {
            const status = getStatus(m)
            const isHuman = m.type === 'human'
            return (
              <div
                key={m.id}
                className={`flex items-center gap-2 px-2 py-1.5 rounded-2xl transition-colors hover:bg-white/[0.05] ${
                  !isHuman ? 'cursor-pointer' : ''
                }`}
                onClick={() => {
                  if (!isHuman) setSelectedMember(m)
                }}
              >
                {!isHuman && (
                  <div className={`w-2 h-2 rounded-full ${status.color}`} title={status.text} />
                )}
                <div className="flex flex-col min-w-0">
                  <span className="text-sm truncate">{m.name}</span>
                  {!isHuman && agentStatus[m.name] && (
                    <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                      {status.label}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 ml-auto shrink-0">
                  {m.role && m.role !== 'member' && (
                    <span
                      className="text-[9px] px-1.5 py-0.5 rounded-full"
                      style={{
                        color: '#00d4aa',
                        backgroundColor: 'rgba(0,212,170,0.1)',
                        border: '1px solid rgba(0,212,170,0.2)',
                      }}
                    >
                      {m.role}
                    </span>
                  )}
                  <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                    {m.type}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </aside>

      {/* Agent Detail Modal */}
      {selectedMember && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}
          onClick={() => setSelectedMember(null)}
        >
          <div
            className="w-full max-w-sm rounded-3xl p-5 space-y-4"
            style={{ backgroundColor: 'var(--bg-elevated)' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-2xl flex items-center justify-center text-lg font-bold"
                  style={{
                    backgroundColor: 'rgba(0,212,170,0.15)',
                    color: '#00d4aa',
                  }}
                >
                  {selectedMember.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="text-sm font-semibold">{selectedMember.name}</div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${getStatus(selectedMember).color}`} />
                    <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                      {getStatus(selectedMember).text}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedMember(null)}
                className="p-1.5 rounded-xl hover:bg-white/10 transition-colors"
                style={{ color: 'var(--text-muted)' }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 6 6 18" /><path d="m6 6 12 12" />
                </svg>
              </button>
            </div>

            {/* Role */}
            <div className="space-y-1">
              <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                Role
              </div>
              <div className="text-sm">{selectedMember.role || 'member'}</div>
            </div>

            {/* Description */}
            {selectedMember.description && (
              <div className="space-y-1">
                <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  Description
                </div>
                <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>
                  {selectedMember.description}
                </div>
              </div>
            )}

            {/* Stats */}
            {memberStats[selectedMember.id] && (
              <div className="space-y-1">
                <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  Stats
                </div>
                <div className="flex gap-4">
                  <div
                    className="flex-1 rounded-2xl px-3 py-2 text-center"
                    style={{ backgroundColor: 'rgba(0,212,170,0.08)' }}
                  >
                    <div className="text-lg font-bold" style={{ color: '#00d4aa' }}>
                      {memberStats[selectedMember.id].message_count}
                    </div>
                    <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                      Messages
                    </div>
                  </div>
                  <div
                    className="flex-1 rounded-2xl px-3 py-2 text-center"
                    style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                  >
                    <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                      {formatTime(memberStats[selectedMember.id].last_message_at)}
                    </div>
                    <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                      Last active
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
