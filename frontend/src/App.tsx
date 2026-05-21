import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { API_BASE, WS_BASE } from './config'
import type { Room, Member, Message } from './types'

import Sidebar from './components/Sidebar'
import ChatHeader from './components/ChatHeader'
import MessageList from './components/MessageList'
import MessageInput from './components/MessageInput'
import MemberList from './components/MemberList'
import Toast from './components/Toast'
import ErrorBoundary from './components/ErrorBoundary'
import { useTheme } from './hooks/useTheme'

export default function App() {
  const { theme, toggleTheme } = useTheme()
  const [rooms, setRooms] = useState<Room[]>([])
  const [currentRoomId, setCurrentRoomId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [agentStatus, setAgentStatus] = useState<Record<string, { process_online: boolean; listening: boolean; last_active: string }>>({})
  const [input, setInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed'>('closed')
  const [myName, setMyName] = useState('human')
  const [showSidebar, setShowSidebar] = useState(false)
  const [showMembers, setShowMembers] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [replyTo, setReplyTo] = useState<Message | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = (message: string, type: 'error' | 'success' = 'error') => {
    if (toastTimer.current) clearTimeout(toastTimer.current)
    setToast({ message, type })
    toastTimer.current = setTimeout(() => setToast(null), 3000)
  }

  // Load rooms
  const loadRooms = useCallback(async () => {
    const r = await fetch(`${API_BASE}/rooms`)
    const data = await r.json()
    setRooms(data)
    if (data.length > 0 && !currentRoomId) {
      setCurrentRoomId(data[0].id)
    }
  }, [currentRoomId])

  useEffect(() => { loadRooms() }, [loadRooms])

  // Load agent status
  const loadAgentStatus = useCallback(async (roomId: number, signal?: AbortSignal) => {
    try {
      const res = await fetch(`${API_BASE}/rooms/${roomId}/agent-status`, { signal })
      if (res.ok) {
        const data = await res.json()
        const map: Record<string, any> = {}
        for (const item of data) map[item.name] = item
        setAgentStatus(map)
      }
    } catch {}
  }, [])

  useEffect(() => {
    if (!currentRoomId) return
    const controller = new AbortController()
    loadAgentStatus(currentRoomId, controller.signal)
    const timer = setInterval(() => loadAgentStatus(currentRoomId, controller.signal), 10000)
    return () => {
      clearInterval(timer)
      controller.abort()
    }
  }, [currentRoomId, loadAgentStatus])

  // Load room data
  const loadRoomData = useCallback(async (roomId: number, signal?: AbortSignal) => {
    const [msgRes, memRes] = await Promise.all([
      fetch(`${API_BASE}/rooms/${roomId}/messages?limit=200`, { signal }),
      fetch(`${API_BASE}/rooms/${roomId}/members`, { signal }),
    ])
    const msgs = await msgRes.json()
    const mems = await memRes.json()
    setMessages(msgs)
    setMembers(mems)
    loadAgentStatus(roomId, signal)
  }, [loadAgentStatus])

  // WebSocket connection
  useEffect(() => {
    if (!currentRoomId) return
    const controller = new AbortController()
    loadRoomData(currentRoomId, controller.signal)

    let ws: WebSocket | null = null
    let reconnectDelay = 1000
    let reconnectAttempts = 0
    const maxReconnectDelay = 30000
    const maxReconnectAttempts = 10
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let shouldReconnect = true

    const connect = () => {
      if (!shouldReconnect) return
      setWsStatus('connecting')
      ws = new WebSocket(`${WS_BASE}/ws/${currentRoomId}`)
      wsRef.current = ws

      ws.onopen = () => {
        setWsStatus('open')
        reconnectDelay = 1000
        reconnectAttempts = 0
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'message_deleted') {
            setMessages((prev) => prev.filter((m) => m.id !== data.id))
            return
          }
          const msg: Message = data
          setMessages((prev) => {
            const idx = prev.findIndex((m) => m.id === msg.id)
            if (idx >= 0) {
              const next = [...prev]
              next[idx] = msg
              return next
            }
            return [...prev, msg]
          })
        } catch {}
      }

      ws.onclose = () => {
        setWsStatus('closed')
        wsRef.current = null
        if (shouldReconnect && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          reconnectTimer = setTimeout(connect, reconnectDelay)
          reconnectDelay = Math.min(reconnectDelay * 2, maxReconnectDelay)
        }
      }

      ws.onerror = () => {}
    }

    connect()

    return () => {
      shouldReconnect = false
      controller.abort()
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (ws) {
        ws.close()
        wsRef.current = null
      }
    }
  }, [currentRoomId, loadRoomData])

  // Send message
  const sendMessage = async () => {
    if (!input.trim() || !currentRoomId || isSending) return
    const content = input.trim()
    setInput('')
    setIsSending(true)

    const room = rooms.find((r) => r.id === currentRoomId)
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (room?.secret) headers['X-Room-Secret'] = room.secret

    try {
      const body: any = { from_name: myName, content }
      if (replyTo) body.reply_to = replyTo.id
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Failed: ${res.status}`)
      }
      setReplyTo(null)
    } catch (e: any) {
      showToast(e.message || 'Send failed')
      setInput(content)
    } finally {
      setIsSending(false)
    }
  }

  const insertMention = (name: string) => {
    const mention = name === 'all' ? '@all ' : `@${name} `
    setInput((prev) => {
      const sep = prev && !prev.endsWith(' ') ? ' ' : ''
      return prev + sep + mention
    })
  }

  // Edit message
  const startEdit = (msg: Message) => {
    setEditingId(msg.id)
  }

  const saveEdit = async (msgId: number, content: string) => {
    if (!content.trim() || !currentRoomId) return
    const room = rooms.find((r) => r.id === currentRoomId)
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (room?.secret) headers['X-Room-Secret'] = room.secret

    try {
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages/${msgId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ content: content.trim() }),
      })
      if (!res.ok) throw new Error('Edit failed')
      setEditingId(null)
    } catch (e: any) {
      showToast(e.message || 'Edit failed')
    }
  }

  // Delete message
  const deleteMsg = async (msgId: number) => {
    if (!currentRoomId) return
    const room = rooms.find((r) => r.id === currentRoomId)
    const headers: Record<string, string> = {}
    if (room?.secret) headers['X-Room-Secret'] = room.secret

    try {
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages/${msgId}`, {
        method: 'DELETE',
        headers,
      })
      if (!res.ok) throw new Error('Delete failed')
      setMessages((prev) => prev.filter((m) => m.id !== msgId))
    } catch (e: any) {
      showToast(e.message || 'Delete failed')
    }
  }

  // Create room
  const createRoom = async () => {
    const name = prompt('Room name:')
    if (!name) return
    const r = await fetch(`${API_BASE}/rooms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    const newRoom = await r.json()
    alert(`Room created! Secret: ${newRoom.secret}\nSave it, you'll need it to send messages.`)
    loadRooms()
  }

  const currentRoom = rooms.find((r) => r.id === currentRoomId)

  const fmtTime = (iso: string) => {
    try {
      const safeIso = iso.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(iso) ? iso : iso + 'Z'
      const d = new Date(safeIso)
      const pad = (n: number) => n.toString().padStart(2, '0')
      return `${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch { return '' }
  }

  const fmtDate = (iso: string) => {
    try {
      const safeIso = iso.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(iso) ? iso : iso + 'Z'
      const d = new Date(safeIso)
      const now = new Date()
      const isToday = d.toDateString() === now.toDateString()
      const isYesterday = new Date(now.getTime() - 86400000).toDateString() === d.toDateString()
      if (isToday) return 'Today'
      if (isYesterday) return 'Yesterday'
      const pad = (n: number) => n.toString().padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    } catch { return '' }
  }

  const filteredMessages = useMemo(() => {
    if (!searchQuery.trim()) return messages
    const q = searchQuery.toLowerCase()
    return messages.filter(
      (msg) =>
        (msg.content || '').toLowerCase().includes(q) ||
        (msg.sender_name || '').toLowerCase().includes(q)
    )
  }, [messages, searchQuery])

  return (
    <ErrorBoundary>
      <div
        className="flex h-screen w-screen overflow-hidden"
        data-theme={theme}
        style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}
      >
        {(showSidebar || showMembers) && (
          <div
            className="fixed inset-0 z-40 lg:hidden"
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            onClick={() => { setShowSidebar(false); setShowMembers(false) }}
          />
        )}

        <Sidebar
          rooms={rooms}
          currentRoomId={currentRoomId}
          myName={myName}
          showSidebar={showSidebar}
          onRoomSelect={(id) => { setCurrentRoomId(id); setShowSidebar(false) }}
          onCreateRoom={createRoom}
          onMyNameChange={setMyName}
          onClose={() => setShowSidebar(false)}
        />

        <main className="flex-1 flex flex-col min-w-0">
          <ChatHeader
            roomName={currentRoom?.name || ''}
            wsStatus={wsStatus}
            theme={theme}
            onToggleTheme={toggleTheme}
            onToggleSidebar={() => setShowSidebar(!showSidebar)}
            onToggleMembers={() => setShowMembers(!showMembers)}
          />

          <div className="px-5 pt-3">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="🔍 Search messages..."
              className="w-full rounded-2xl px-4 py-2 text-sm outline-none transition-all placeholder-white/30 liquid-glass focus:border-[#00d4aa]/40"
            />
          </div>

          <MessageList
            messages={messages}
            filteredMessages={filteredMessages}
            myName={myName}
            editingId={editingId}
            onStartEdit={startEdit}
            onSaveEdit={saveEdit}
            onCancelEdit={() => { setEditingId(null) }}
            onDelete={deleteMsg}
            onReply={setReplyTo}
            fmtTime={fmtTime}
            fmtDate={fmtDate}
          />

          <MessageInput
            input={input}
            onInputChange={setInput}
            onSend={sendMessage}
            isSending={isSending}
            myName={myName}
            members={members}
            replyTo={replyTo}
            onCancelReply={() => setReplyTo(null)}
            onInsertMention={insertMention}
          />
        </main>

        <MemberList members={members} agentStatus={agentStatus} showMembers={showMembers} />

        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      </div>
    </ErrorBoundary>
  )
}
