import type { Room } from '../types'

interface SidebarProps {
  rooms: Room[]
  currentRoomId: number | null
  myName: string
  showSidebar: boolean
  onRoomSelect: (id: number) => void
  onCreateRoom: () => void
  onMyNameChange: (name: string) => void
  onClose: () => void
}

export default function Sidebar({
  rooms,
  currentRoomId,
  myName,
  showSidebar,
  onRoomSelect,
  onCreateRoom,
  onMyNameChange,
}: SidebarProps) {
  return (
    <aside
      className={`fixed lg:static inset-y-0 left-0 z-50 w-64 flex-shrink-0 flex flex-col transition-transform duration-300 lg:translate-x-0 ${showSidebar ? 'translate-x-0' : '-translate-x-full'}`}
      style={{ borderRadius: '0 24px 24px 0', backgroundColor: 'var(--bg-elevated)' }}
    >
      <div className="p-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-wide text-[#00d4aa]">🤖 Agent Coop</h2>
      </div>
      <div className="p-3">
        <button
          onClick={onCreateRoom}
          className="w-full py-2 px-3 rounded-2xl text-xs font-medium transition-all hover:bg-white/10 liquid-glass"
        >
          + Create Room
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
        {rooms.map((room) => (
          <button
            key={room.id}
            onClick={() => onRoomSelect(room.id)}
            className={`w-full text-left px-3 py-2.5 rounded-2xl text-sm transition-all ${
              room.id === currentRoomId ? 'text-[#00d4aa]' : 'hover:bg-white/[0.05]'
            }`}
            style={
              room.id === currentRoomId
                ? { backgroundColor: 'rgba(0,212,170,0.12)' }
                : { color: 'var(--text-muted)' }
            }
          >
            <span className="font-medium">#</span> {room.name}
          </button>
        ))}
      </div>
      <div className="p-3">
        <div className="text-[10px] mb-1" style={{ color: 'var(--text-muted)' }}>
          Your Name
        </div>
        <input
          value={myName}
          onChange={(e) => onMyNameChange(e.target.value)}
          className="w-full rounded-xl px-3 py-1.5 text-xs outline-none liquid-glass focus:border-[#00d4aa]/50 transition-all"
        />
      </div>
    </aside>
  )
}
