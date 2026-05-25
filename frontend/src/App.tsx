import { useEffect, useRef, useState, useCallback, useMemo, lazy, Suspense } from 'react'
import { API_BASE, WS_BASE } from './config'
import type { Room, Member, Message, AgentStatus, MemberStats } from './types'

import ChatHeader from './components/ChatHeader'
import MessageList from './components/MessageList'
import MessageInput from './components/MessageInput'
import Toast from './components/Toast'
import ErrorBoundary from './components/ErrorBoundary'
import { useTheme } from './hooks/useTheme'
import { useMemberToken } from './hooks/useMemberToken'

const Sidebar = lazy(() => import('./components/Sidebar'))
const MemberList = lazy(() => import('./components/MemberList'))

export default function App() {
  const { theme, setTheme } = useTheme()
  const [rooms, setRooms] = useState<Room[]>([])
  const [currentRoomId, setCurrentRoomId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [agentStatus, setAgentStatus] = useState<Record<string, AgentStatus>>({})
  const [input, setInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed'>('closed')
  const { token: memberToken, memberName, saveToken, clearToken } = useMemberToken(currentRoomId)
  const [showSidebar, setShowSidebar] = useState(false)
  const [showMembers, setShowMembers] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [mentionTo, setMentionTo] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState('')
  const [announcement, setAnnouncement] = useState('')
  const [memberStats, setMemberStats] = useState<Record<number, MemberStats>>({})
  const [searchResults, setSearchResults] = useState<Message[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [unreadCounts, setUnreadCounts] = useState<Record<number, number>>({})
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const draftTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = (message: string, type: 'error' | 'success' = 'error') => {
    if (toastTimer.current) clearTimeout(toastTimer.current)
    setToast({ message, type })
    toastTimer.current = setTimeout(() => setToast(null), 3000)
  }

  // Load rooms
  const loadRooms = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/rooms`, { credentials: 'include' })
      const data = await r.json()
      if (!Array.isArray(data)) {
        setRooms([])
        return
      }
      setRooms(data)
      if (data.length > 0 && !currentRoomId) {
        setCurrentRoomId(data[0].id)
      }
    } catch {
      setRooms([])
    }
  }, [currentRoomId])

  useEffect(() => { loadRooms() }, [loadRooms])

  // Load unread count for a room
  const loadUnreadCount = useCallback(async (roomId: number) => {
    try {
      const headers: Record<string, string> = {}
      if (memberToken) headers['X-Member-Token'] = memberToken
      const res = await fetch(`${API_BASE}/rooms/${roomId}/messages/unread-count`, { credentials: 'include', headers })
      if (res.ok) {
        const data = await res.json()
        const count = data.unread_count || 0
        setUnreadCounts(prev => {
          if (prev[roomId] === count) return prev
          return { ...prev, [roomId]: count }
        })
      }
    } catch {}
  }, [memberToken])

  // Load unread counts for all rooms
  useEffect(() => {
    rooms.forEach(room => loadUnreadCount(room.id))
  }, [rooms, loadUnreadCount])

  // Load agent status
  const loadAgentStatus = useCallback(async (roomId: number, signal?: AbortSignal) => {
    try {
      const headers: Record<string, string> = {}
      if (memberToken) headers['X-Member-Token'] = memberToken
      const res = await fetch(`${API_BASE}/rooms/${roomId}/agent-status`, { signal, credentials: 'include', headers })
      if (res.ok) {
        const data = await res.json()
        if (!Array.isArray(data)) return
        const map: Record<string, any> = {}
        for (const item of data) map[item.name] = item
        setAgentStatus(map)
      }
    } catch {}
  }, [memberToken])

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

  // Load announcement when room changes
  useEffect(() => {
    if (!currentRoomId) {
      setAnnouncement('')
      return
    }
    // Clear search when switching rooms
    setSearchQuery('')
    setSearchResults([])
    setShowSearch(false)
    const controller = new AbortController()
    const headers: Record<string, string> = {}
    if (memberToken) headers['X-Member-Token'] = memberToken
    fetch(`${API_BASE}/rooms/${currentRoomId}/announcement`, {
      signal: controller.signal,
      credentials: 'include',
      headers,
    })
      .then((r) => (r.ok ? r.text() : ''))
      .then((text) => setAnnouncement(text))
      .catch(() => setAnnouncement(''))
    return () => controller.abort()
  }, [currentRoomId, memberToken])

  // Debounced search
  useEffect(() => {
    if (!currentRoomId || !searchQuery.trim()) {
      setSearchResults([])
      setIsSearching(false)
      return
    }
    if (searchTimer.current) clearTimeout(searchTimer.current)
    setIsSearching(true)
    searchTimer.current = setTimeout(async () => {
      try {
        const headers: Record<string, string> = {}
        if (memberToken) headers['X-Member-Token'] = memberToken
        const res = await fetch(
          `${API_BASE}/rooms/${currentRoomId}/search?q=${encodeURIComponent(searchQuery.trim())}&limit=50`,
          { credentials: 'include', headers }
        )
        if (res.ok) {
          const data = await res.json()
          setSearchResults(Array.isArray(data) ? data : [])
        }
      } catch {
        setSearchResults([])
      } finally {
        setIsSearching(false)
      }
    }, 300)
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current)
    }
  }, [searchQuery, currentRoomId, memberToken])

  // Load draft when room changes
  useEffect(() => {
    if (!currentRoomId) {
      setInput('')
      return
    }
    const headers: Record<string, string> = {}
    if (memberToken) headers['X-Member-Token'] = memberToken
    fetch(`${API_BASE}/rooms/${currentRoomId}/draft`, { credentials: 'include', headers })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.content) setInput(data.content)
        else setInput('')
      })
      .catch(() => setInput(''))
  }, [currentRoomId, memberToken])

  // Auto-save draft
  useEffect(() => {
    if (!currentRoomId) return
    if (draftTimer.current) clearTimeout(draftTimer.current)
    draftTimer.current = setTimeout(async () => {
      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        }
        if (memberToken) headers['X-Member-Token'] = memberToken
        if (input.trim()) {
          await fetch(`${API_BASE}/rooms/${currentRoomId}/draft`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({ content: input }),
            credentials: 'include',
          })
        } else {
          await fetch(`${API_BASE}/rooms/${currentRoomId}/draft`, {
            method: 'DELETE',
            headers,
            credentials: 'include',
          })
        }
      } catch {}
    }, 2000)
    return () => {
      if (draftTimer.current) clearTimeout(draftTimer.current)
    }
  }, [input, currentRoomId, memberToken])

  // Mark room as read
  const markRoomRead = useCallback(async (roomId: number) => {
    setUnreadCounts(prev => ({ ...prev, [roomId]: 0 }))
    try {
      const headers: Record<string, string> = {}
      if (memberToken) headers['X-Member-Token'] = memberToken
      // Get latest message and mark it as read
      const res = await fetch(`${API_BASE}/rooms/${roomId}/messages?limit=1`, { credentials: 'include', headers })
      if (res.ok) {
        const msgs = await res.json()
        if (Array.isArray(msgs) && msgs.length > 0) {
          await fetch(`${API_BASE}/rooms/${roomId}/messages/read?message_id=${msgs[0].id}`, {
            method: 'POST', credentials: 'include', headers
          })
        }
      }
    } catch {}
  }, [memberToken])

  // Mark initial room as read on first load
  const hasMarkedInitialRead = useRef(false)
  useEffect(() => {
    if (currentRoomId && !hasMarkedInitialRead.current) {
      hasMarkedInitialRead.current = true
      markRoomRead(currentRoomId)
    }
  }, [currentRoomId, markRoomRead])

  // Load room data
  const loadRoomData = useCallback(async (roomId: number, signal?: AbortSignal) => {
    const headers: Record<string, string> = {}
    if (memberToken) headers['X-Member-Token'] = memberToken
    const [msgRes, memRes, statsRes] = await Promise.all([
      fetch(`${API_BASE}/rooms/${roomId}/messages?limit=200`, { signal, credentials: 'include', headers }),
      fetch(`${API_BASE}/rooms/${roomId}/members`, { signal, credentials: 'include', headers }),
      fetch(`${API_BASE}/rooms/${roomId}/members/stats`, { signal, credentials: 'include', headers }),
    ])
    const msgs = await msgRes.json()
    const mems = await memRes.json()
    const stats = await statsRes.json()
    setMessages(Array.isArray(msgs) ? msgs : [])
    setMembers(Array.isArray(mems) ? mems : [])
    if (Array.isArray(stats)) {
      const map: Record<number, MemberStats> = {}
      for (const s of stats) map[s.member_id] = s
      setMemberStats(map)
    }
    loadAgentStatus(roomId, signal)
  }, [loadAgentStatus, memberToken])

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
          // Ignore ping/pong/heartbeat and malformed messages
          if (data.type === 'ping' || data.type === 'pong' || data.type === 'heartbeat' || data.id == null) {
            return
          }
          const msg: Message = data
          // Update unread count if message is for a different room
          if (msg.room_id && msg.room_id !== currentRoomId) {
            setUnreadCounts((prev) => ({ ...prev, [msg.room_id]: (prev[msg.room_id] || 0) + 1 }))
          }
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

  // Upload files and insert markdown into input
  const uploadFiles = async (files: FileList) => {
    if (!currentRoomId) return
    const room = rooms.find((r) => r.id === currentRoomId)

    setIsUploading(true)
    const uploaded: string[] = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setUploadProgress(`Uploading ${file.name} (${i + 1}/${files.length})...`)

      const formData = new FormData()
      formData.append('file', file)

      try {
        const headers: Record<string, string> = {}
        if (room?.secret) headers['X-Room-Secret'] = room.secret
        if (memberToken) headers['X-Member-Token'] = memberToken

        const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/attachments`, {
          method: 'POST',
          headers,
          body: formData,
          credentials: 'include',
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || `Upload failed: ${res.status}`)
        }
        const data = await res.json()
        const isImage = file.type.startsWith('image/')
        const markdown = isImage
          ? `![${file.name}](${data.url})`
          : `[📎 ${file.name}](${data.url})`
        uploaded.push(markdown)
      } catch (e: any) {
        showToast(e.message || `Failed to upload ${file.name}`)
      }
    }

    if (uploaded.length > 0) {
      setInput((prev) => {
        const sep = prev && !prev.endsWith('\n') && prev.length > 0 ? '\n\n' : ''
        return prev + sep + uploaded.join('\n\n') + '\n\n'
      })
    }

    setIsUploading(false)
    setUploadProgress('')
  }

  // Send message
  const sendMessage = async () => {
    if (!input.trim() || !currentRoomId || isSending || isUploading) return
    const content = input.trim()
    setInput('')
    setIsSending(true)

    const room = rooms.find((r) => r.id === currentRoomId)
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (room?.secret) headers['X-Room-Secret'] = room.secret
    if (memberToken) headers['X-Member-Token'] = memberToken

    try {
      const body: any = { content }
      if (mentionTo) body.to_name = mentionTo
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        credentials: 'include',
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Failed: ${res.status}`)
      }
      setMentionTo(null)
      // Delete draft after successful send
      try {
        const draftHeaders: Record<string, string> = {}
        if (memberToken) draftHeaders['X-Member-Token'] = memberToken
        fetch(`${API_BASE}/rooms/${currentRoomId}/draft`, {
          method: 'DELETE',
          headers: draftHeaders,
          credentials: 'include',
        })
      } catch {}
    } catch (e: any) {
      showToast(e.message || 'Send failed')
      setInput(content)
    } finally {
      setIsSending(false)
    }
  }

  const insertMention = (name: string) => {
    setMentionTo(name)
    const mention = name === 'all' ? '@all ' : `@${name} `
    setInput((prev) => {
      const sep = prev && !prev.endsWith(' ') ? ' ' : ''
      return prev + sep + mention
    })
  }

  // Join room to get member token
  const joinRoom = async (roomId: number, name: string, secret: string) => {
    if (!roomId || !name.trim()) return
    const room = rooms.find((r) => r.id === roomId)
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (room?.secret || secret) headers['X-Room-Secret'] = secret || room?.secret || ''

    try {
      const res = await fetch(`${API_BASE}/rooms/${roomId}/join`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ name: name.trim(), type: 'human' }),
        credentials: 'include',
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Join failed: ${res.status}`)
      }
      const data = await res.json()
      saveToken(roomId, name.trim(), data.token)
      showToast(`Joined as ${name.trim()}!`, 'success')
      setCurrentRoomId(roomId)
      // Only reload members, not messages (WebSocket handles message updates)
      const memHeaders: Record<string, string> = {}
      if (data.token) memHeaders['X-Member-Token'] = data.token
      const memRes = await fetch(`${API_BASE}/rooms/${roomId}/members`, { credentials: 'include', headers: memHeaders })
      const mems = await memRes.json()
      setMembers(Array.isArray(mems) ? mems : [])
      loadAgentStatus(roomId)
      loadRooms()
    } catch (e: any) {
      showToast(e.message || 'Join failed')
    }
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
    if (memberToken) headers['X-Member-Token'] = memberToken

    try {
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages/${msgId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ content: content.trim() }),
        credentials: 'include',
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
    if (memberToken) headers['X-Member-Token'] = memberToken

    try {
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages/${msgId}`, {
        method: 'DELETE',
        headers,
        credentials: 'include',
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
      credentials: 'include',
    })
    const newRoom = await r.json()
    alert(`Room created! Secret: ${newRoom.secret}\nSave it, you'll need it to send messages.`)
    loadRooms()
  }

  const currentRoom = rooms.find((r) => r.id === currentRoomId)

  const myRole = members.find((m) => m.name === memberName)?.role || 'member'
  const canGenerateInvite = myRole === 'owner' || myRole === 'admin'

  const generateInvite = async () => {
    if (!currentRoomId) return
    try {
      const headers: Record<string, string> = {}
      if (memberToken) headers['X-Member-Token'] = memberToken
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/invite`, { credentials: 'include', headers })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to generate invite')
      }
      const data = await res.json()
      await navigator.clipboard.writeText(data.invite_url)
      showToast('Invite link copied to clipboard!', 'success')
    } catch (e: any) {
      showToast(e.message || 'Failed to generate invite')
    }
  }

  const cancelEdit = useCallback(() => setEditingId(null), [])

  const fmtTime = (iso: string | null | undefined) => {
    if (!iso) return ''
    try {
      const safeIso = iso.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(iso) ? iso : iso + 'Z'
      const d = new Date(safeIso)
      const pad = (n: number) => n.toString().padStart(2, '0')
      return `${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch { return '' }
  }

  const fmtDate = (iso: string | null | undefined) => {
    if (!iso) return ''
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
    if (searchResults.length > 0) return searchResults
    // Fallback to client-side filtering if backend search fails/empty
    const q = searchQuery.toLowerCase()
    return messages.filter(
      (msg) =>
        (msg.content || '').toLowerCase().includes(q) ||
        (msg.sender_name || '').toLowerCase().includes(q)
    )
  }, [messages, searchQuery, searchResults])

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

        <Suspense fallback={null}>
          <Sidebar
            rooms={rooms}
            currentRoomId={currentRoomId}
            myName={memberName}
            memberToken={memberToken}
            showSidebar={showSidebar}
            unreadCounts={unreadCounts}
            onRoomSelect={(id) => { setCurrentRoomId(id); setShowSidebar(false); markRoomRead(id) }}
            onCreateRoom={createRoom}
            onMyNameChange={() => {
              if (memberToken) {
                // Already joined, need to re-join with new name
                clearToken()
              }
            }}
            onJoinRoom={joinRoom}
            onClose={() => setShowSidebar(false)}
          />
        </Suspense>

        <main className="flex-1 flex flex-col min-w-0">
          <ChatHeader
            roomName={currentRoom?.name || ''}
            wsStatus={wsStatus}
            theme={theme}
            onThemeChange={setTheme}
            onToggleSidebar={() => setShowSidebar(!showSidebar)}
            onToggleMembers={() => setShowMembers(!showMembers)}
            agentStatus={agentStatus}
            canGenerateInvite={canGenerateInvite}
            onGenerateInvite={generateInvite}
          />

          {/* Search bar - expandable */}
          <div className="px-5 pt-3 relative flex items-center justify-end">
            {!showSearch ? (
              <button
                onClick={() => setShowSearch(true)}
                className="p-2.5 rounded-xl liquid-glass btn-press transition-all hover:brightness-125"
                style={{ color: 'var(--text-secondary)' }}
                title="Search messages"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.3-4.3"/>
                </svg>
              </button>
            ) : (
              <div className="search-expand-enter-active w-full flex items-center gap-2">
                <div className="flex-1 relative">
                  {/* Search icon inside input */}
                  <div className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--text-muted)' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"/>
                      <path d="m21 21-4.3-4.3"/>
                    </svg>
                  </div>
                  <input
                    autoFocus
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') {
                        setSearchQuery('')
                        setShowSearch(false)
                      }
                    }}
                    placeholder="Search messages..."
                    className="w-full rounded-xl pl-9 pr-9 py-2 text-sm outline-none transition-all"
                    style={{
                      color: 'var(--text-primary)',
                      backgroundColor: 'var(--dark-surface-1)',
                      border: '1px solid var(--border-color)',
                    }}
                  />
                  {searchQuery ? (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-full btn-press transition-all hover:bg-white/10"
                      style={{ color: 'var(--text-muted)' }}
                      title="Clear search"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                      </svg>
                    </button>
                  ) : (
                    <button
                      onClick={() => { setSearchQuery(''); setShowSearch(false) }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-full btn-press transition-all hover:bg-white/10"
                      style={{ color: 'var(--text-muted)' }}
                      title="Close search"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            )}
            {showSearch && (
              <div className="absolute left-5 bottom-0 translate-y-full mt-1 text-[10px] px-1 z-10" style={{ color: 'var(--text-muted)' }}>
                {isSearching ? 'Searching...' : searchQuery ? `${filteredMessages.length} result${filteredMessages.length !== 1 ? 's' : ''}` : ''}
              </div>
            )}
          </div>

          <MessageList
            messages={messages}
            filteredMessages={filteredMessages}
            myName={memberName}
            members={members}
            editingId={editingId}
            onStartEdit={startEdit}
            onSaveEdit={saveEdit}
            onCancelEdit={cancelEdit}
            onDelete={deleteMsg}
            fmtTime={fmtTime}
            fmtDate={fmtDate}
          />

          <MessageInput
            input={input}
            onInputChange={setInput}
            onSend={sendMessage}
            isSending={isSending}
            myName={memberName}
            members={members}
            onInsertMention={insertMention}
            onUploadFiles={uploadFiles}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
          />
        </main>

        <Suspense fallback={null}>
          <MemberList
            members={members}
            agentStatus={agentStatus}
            showMembers={showMembers}
            announcement={announcement}
            memberStats={memberStats}
            currentRoomId={currentRoomId}
            memberToken={memberToken}
            myName={memberName}
            onRefreshMembers={() => currentRoomId && loadRoomData(currentRoomId)}
          />
        </Suspense>

        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      </div>
    </ErrorBoundary>
  )
}
