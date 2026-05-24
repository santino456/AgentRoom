import { useState } from 'react'
import type { Room } from '../types'

interface SidebarProps {
  rooms: Room[]
  currentRoomId: number | null
  myName: string
  memberToken: string
  showSidebar: boolean
  unreadCounts?: Record<number, number>
  onRoomSelect: (id: number) => void
  onCreateRoom: () => void
  onMyNameChange: (name: string) => void
  onJoinRoom: (roomId: number, name: string, secret: string) => void
  onClose: () => void
}

export default function Sidebar({
  rooms,
  currentRoomId,
  myName,
  memberToken,
  showSidebar,
  unreadCounts,
  onRoomSelect,
  onCreateRoom,
  onJoinRoom,
}: SidebarProps) {
  const [joinName, setJoinName] = useState('')
  const [joinRoomId, setJoinRoomId] = useState('')
  const [joinSecret, setJoinSecret] = useState('')
  const [showJoinForm, setShowJoinForm] = useState(false)
  const [isJoiningAnotherRoom, setIsJoiningAnotherRoom] = useState(false)
  const isJoined = !!memberToken && !!myName
  const needsRoomId = !currentRoomId || isJoiningAnotherRoom

  const handleJoin = () => {
    const roomId = needsRoomId ? parseInt(joinRoomId.trim(), 10) : (currentRoomId || 0)
    if (!roomId || !joinName.trim()) return
    onJoinRoom(roomId, joinName.trim(), joinSecret.trim())
    setShowJoinForm(false)
    setIsJoiningAnotherRoom(false)
    setJoinName('')
    setJoinRoomId('')
    setJoinSecret('')
  }

  const canJoin = joinName.trim() && (!needsRoomId || joinRoomId.trim())

  return (
    <aside
      className={`fixed lg:static inset-y-0 left-0 z-50 w-64 flex-shrink-0 flex flex-col transition-transform duration-300 lg:translate-x-0 ${showSidebar ? 'translate-x-0' : '-translate-x-full'}`}
      style={{
        borderRadius: '0 24px 24px 0',
        backgroundColor: 'var(--bg-elevated)',
        borderRight: '1px solid var(--border-color)',
      }}
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center text-sm"
            style={{
              background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
            }}
          >
            🤖
          </div>
          <h2
            className="text-sm font-semibold tracking-tight"
            style={{
              background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Agent Coop
          </h2>
        </div>
      </div>

      {/* Create Room Button */}
      <div className="px-3 pb-2">
        <button
          onClick={onCreateRoom}
          className="w-full py-2.5 px-3 rounded-xl text-xs font-medium transition-all btn-press"
          style={{
            backgroundColor: 'var(--accent-primary)',
            color: '#ffffff',
          }}
        >
          <span className="flex items-center justify-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14"/><path d="M12 5v14"/>
            </svg>
            New Room
          </span>
        </button>
      </div>

      {/* Join Room Button */}
      <div className="px-3 pb-3">
        <button
          onClick={() => { setShowJoinForm(true); setIsJoiningAnotherRoom(true); setJoinName(myName) }}
          className="w-full py-2 px-3 rounded-xl text-xs font-medium transition-all btn-press"
          style={{
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-color)',
          }}
        >
          <span className="flex items-center justify-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
              <polyline points="10 17 15 12 10 7"/>
              <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
            Join Room
          </span>
        </button>
      </div>

      {/* Room List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-0.5">
        <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          Rooms
        </div>
        {rooms.length === 0 && (
          <div className="px-3 py-4 text-xs text-center" style={{ color: 'var(--text-muted)' }}>
            还没有加入任何房间
            <br />
            <span className="text-[10px]">点击下方 Join Room 加入</span>
          </div>
        )}
        {rooms.map((room) => {
          const unread = unreadCounts?.[room.id] || 0
          const showUnread = unread > 0 && room.id !== currentRoomId && rooms.length > 1
          return (
            <button
              key={room.id}
              onClick={() => onRoomSelect(room.id)}
              className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all btn-press sidebar-item-glow relative ${
                room.id === currentRoomId ? 'font-medium' : ''
              }`}
              style={
                room.id === currentRoomId
                  ? {
                      backgroundColor: 'rgba(0, 113, 227, 0.12)',
                      color: 'var(--accent-primary)',
                    }
                  : { color: 'var(--text-secondary)' }
              }
            >
              <span className="relative z-10 flex items-center gap-2">
                <span
                  className="text-xs"
                  style={room.id === currentRoomId ? { color: 'var(--accent-primary)' } : {}}
                >
                  #
                </span>
                <span className="truncate flex-1">{room.name}</span>
                {showUnread && (
                  <span
                    className="shrink-0 min-w-[18px] h-[18px] px-1 rounded-full flex items-center justify-center text-[10px] font-bold"
                    style={{ backgroundColor: 'var(--accent-coral)', color: '#fff' }}
                  >
                    {unread > 99 ? '99+' : unread}
                  </span>
                )}
                {room.id === currentRoomId && (
                  <span
                    className="ml-auto w-1.5 h-1.5 rounded-full status-pulse"
                    style={{ backgroundColor: 'var(--accent-primary)' }}
                  />
                )}
              </span>
            </button>
          )
        })}
      </div>

      {/* Member Identity */}
      <div className="p-3" style={{ borderTop: '1px solid var(--border-color)' }}>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>
          Your Identity
        </div>

        {!showJoinForm ? (
          isJoined ? (
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl" style={{ backgroundColor: 'var(--bg-surface)' }}>
              <span className="text-sm">👤</span>
              <span className="text-sm font-medium flex-1 truncate">{myName}</span>
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: 'var(--accent-green)' }}
              />
            </div>
          ) : (
            <button
              onClick={() => setShowJoinForm(true)}
              className="w-full py-2 px-3 rounded-xl text-xs font-medium transition-all btn-press"
              style={{
                backgroundColor: 'var(--accent-primary)',
                color: '#ffffff',
              }}
            >
              Join Room
            </button>
          )
        ) : (
          <div className="flex flex-col gap-2">
            {needsRoomId && (
              <input
                value={joinRoomId}
                onChange={(e) => setJoinRoomId(e.target.value)}
                placeholder="Room ID (e.g. 1)"
                className="w-full rounded-xl px-3 py-2 text-xs outline-none transition-all"
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                }}
              />
            )}
            <input
              value={joinName}
              onChange={(e) => setJoinName(e.target.value)}
              placeholder="Enter your name"
              className="w-full rounded-xl px-3 py-2 text-xs outline-none transition-all"
              style={{
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
              }}
            />
            <input
              value={joinSecret}
              onChange={(e) => setJoinSecret(e.target.value)}
              placeholder="Room secret (first-time only)"
              type="password"
              className="w-full rounded-xl px-3 py-2 text-xs outline-none transition-all"
              style={{
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
              }}
            />
            <div className="flex gap-2">
              <button
                onClick={() => { setShowJoinForm(false); setIsJoiningAnotherRoom(false); setJoinName(''); setJoinRoomId(''); setJoinSecret('') }}
                className="flex-1 py-1.5 rounded-xl text-xs transition-all btn-press"
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  color: 'var(--text-secondary)',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleJoin}
                disabled={!canJoin}
                className="flex-1 py-1.5 rounded-xl text-xs font-medium transition-all btn-press disabled:opacity-30"
                style={{
                  backgroundColor: 'var(--accent-primary)',
                  color: '#ffffff',
                }}
              >
                Join
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
