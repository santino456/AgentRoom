import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { API_BASE, WS_BASE } from './config'

// Markdown 渲染组件（提取到外部避免重复创建）
const markdownComponents = {
  code({ className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || '')
    return match ? (
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={match[1]}
        PreTag="div"
        customStyle={{ margin: 0, borderRadius: '0.5rem', fontSize: '0.8rem' }}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <code className="px-1.5 py-0.5 rounded text-xs font-mono" style={{ backgroundColor: 'var(--code-bg)', color: 'var(--code-text)' }} {...props}>
        {children}
      </code>
    )
  },
  p: ({ children }: any) => <p className="mb-1 last:mb-0">{children}</p>,
  h1: ({ children }: any) => <h1 className="text-lg font-bold mb-1">{children}</h1>,
  h2: ({ children }: any) => <h2 className="text-base font-bold mb-1">{children}</h2>,
  h3: ({ children }: any) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
  ul: ({ children }: any) => <ul className="list-disc pl-4 mb-1">{children}</ul>,
  ol: ({ children }: any) => <ol className="list-decimal pl-4 mb-1">{children}</ol>,
  li: ({ children }: any) => <li className="mb-0.5">{children}</li>,
  a: ({ href, children }: any) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#00d4aa] underline hover:opacity-80">
      {children}
    </a>
  ),
  blockquote: ({ children }: any) => (
    <blockquote className="border-l-2 border-[#00d4aa] pl-3 my-1 italic" style={{ color: 'var(--text-secondary)' }}>{children}</blockquote>
  ),
  hr: () => <hr className="my-2" style={{ borderColor: 'var(--border-color)' }} />,
  table: ({ children }: any) => (
    <div className="overflow-x-auto my-1">
      <table className="w-full text-xs border-collapse" style={{ borderColor: 'var(--table-border)' }}>{children}</table>
    </div>
  ),
  thead: ({ children }: any) => <thead style={{ backgroundColor: 'var(--table-head-bg)' }}>{children}</thead>,
  th: ({ children }: any) => <th className="px-2 py-1 text-left" style={{ border: '1px solid var(--table-border)' }}>{children}</th>,
  td: ({ children }: any) => <td className="px-2 py-1" style={{ border: '1px solid var(--table-border)' }}>{children}</td>,
}

const MemoizedMarkdown = React.memo(({ content }: { content: string }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
    {content}
  </ReactMarkdown>
))

interface Room {
  id: number
  name: string
  secret: string
  created_at: string
}

interface Member {
  id: number
  name: string
  type: string
  last_active: string
}

interface Message {
  id: number
  room_id: number
  sender_name: string | null
  content: string
  to_name: string | null
  msg_type: string
  created_at: string
}

export default function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('agent-coop-theme')
    if (saved === 'light' || saved === 'dark') return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })
  const [rooms, setRooms] = useState<Room[]>([])
  const [currentRoomId, setCurrentRoomId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [agentStatus, setAgentStatus] = useState<Record<string, {process_online: boolean, listening: boolean, last_active: string}>>({})
  const [input, setInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed'>('closed')
  const [myName, setMyName] = useState('human')
  const [showSidebar, setShowSidebar] = useState(false)
  const [showMembers, setShowMembers] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [toast, setToast] = useState<{message: string, type: 'error' | 'success'} | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editContent, setEditContent] = useState('')
  const [hoverMsgId, setHoverMsgId] = useState<number | null>(null)
  const [replyTo, setReplyTo] = useState<Message | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 加载 Agent 状态
  const loadAgentStatus = useCallback(async (roomId: number) => {
    try {
      const res = await fetch(`${API_BASE}/rooms/${roomId}/agent-status`)
      if (res.ok) {
        const data = await res.json()
        const map: Record<string, any> = {}
        for (const item of data) {
          map[item.name] = item
        }
        setAgentStatus(map)
      }
    } catch {}
  }, [])

  const showToast = (message: string, type: 'error' | 'success' = 'error') => {
    if (toastTimer.current) clearTimeout(toastTimer.current)
    setToast({ message, type })
    toastTimer.current = setTimeout(() => setToast(null), 3000)
  }

  // 主题切换
  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('agent-coop-theme', next)
  }

  // 回复消息
  const startReply = (msg: Message) => {
    setReplyTo(msg)
    setHoverMsgId(null)
    inputRef.current?.focus()
  }

  const cancelReply = () => {
    setReplyTo(null)
  }

  // 加载房间列表
  const loadRooms = useCallback(async () => {
    const r = await fetch(`${API_BASE}/rooms`)
    const data = await r.json()
    setRooms(data)
    if (data.length > 0 && !currentRoomId) {
      setCurrentRoomId(data[0].id)
    }
  }, [currentRoomId])

  useEffect(() => { loadRooms() }, [loadRooms])

  // 定期轮询 Agent 状态
  useEffect(() => {
    if (!currentRoomId) return
    loadAgentStatus(currentRoomId)
    const timer = setInterval(() => loadAgentStatus(currentRoomId), 10000)
    return () => clearInterval(timer)
  }, [currentRoomId, loadAgentStatus])

  // 加载房间数据和成员
  const loadRoomData = useCallback(async (roomId: number) => {
    const [msgRes, memRes] = await Promise.all([
      fetch(`${API_BASE}/rooms/${roomId}/messages?limit=200`),
      fetch(`${API_BASE}/rooms/${roomId}/members`),
    ])
    const msgs = await msgRes.json()
    const mems = await memRes.json()
    setMessages(msgs)
    setMembers(mems)
    loadAgentStatus(roomId)
  }, [loadAgentStatus])

  // WebSocket 连接（含自动重连）
  useEffect(() => {
    if (!currentRoomId) return
    loadRoomData(currentRoomId)

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
          // 删除消息事件
          if (data.type === 'message_deleted') {
            setMessages(prev => prev.filter(m => m.id !== data.id))
            return
          }
          const msg: Message = data
          setMessages(prev => {
            const idx = prev.findIndex(m => m.id === msg.id)
            if (idx >= 0) {
              // 更新已有消息（编辑后广播）
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

      ws.onerror = () => {
        // 错误时让 onclose 处理重连
      }
    }

    connect()

    return () => {
      shouldReconnect = false
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (ws) {
        ws.close()
        wsRef.current = null
      }
    }
  }, [currentRoomId, loadRoomData])

  // 自动滚动到底部（只在新增消息时）
  const prevMsgCount = useRef(0)
  useEffect(() => {
    if (messages.length > prevMsgCount.current) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    prevMsgCount.current = messages.length
  }, [messages])

  // 发送消息
  const sendMessage = async () => {
    if (!input.trim() || !currentRoomId || isSending) return
    const content = input.trim()
    setInput('')
    setIsSending(true)

    const room = rooms.find(r => r.id === currentRoomId)
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (room?.secret) {
      headers['X-Room-Secret'] = room.secret
    }

    try {
      const body: any = { from_name: myName, content }
      if (replyTo) {
        body.reply_to = replyTo.id
      }
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `发送失败: ${res.status}`)
      }
      setReplyTo(null)
    } catch (e: any) {
      showToast(e.message || '发送失败，请检查网络')
      setInput(content) // 恢复输入内容
    } finally {
      setIsSending(false)
    }
  }

  const insertMention = (name: string) => {
    const mention = name === 'all' ? '@all ' : `@${name} `
    setInput(prev => {
      const sep = prev && !prev.endsWith(' ') ? ' ' : ''
      return prev + sep + mention
    })
    inputRef.current?.focus()
  }

  // 开始编辑消息
  const startEdit = (msg: Message) => {
    setEditingId(msg.id)
    setEditContent(msg.content)
    setHoverMsgId(null)
  }

  // 保存编辑
  const saveEdit = async () => {
    if (!editContent.trim() || !currentRoomId || !editingId) return
    const room = rooms.find(r => r.id === currentRoomId)
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (room?.secret) headers['X-Room-Secret'] = room.secret

    try {
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages/${editingId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ content: editContent.trim() }),
      })
      if (!res.ok) throw new Error('编辑失败')
      setEditingId(null)
      setEditContent('')
    } catch (e: any) {
      showToast(e.message || '编辑失败')
    }
  }

  // 删除消息
  const deleteMsg = async (msgId: number) => {
    if (!currentRoomId) return
    const room = rooms.find(r => r.id === currentRoomId)
    const headers: Record<string, string> = {}
    if (room?.secret) headers['X-Room-Secret'] = room.secret

    try {
      const res = await fetch(`${API_BASE}/rooms/${currentRoomId}/messages/${msgId}`, {
        method: 'DELETE',
        headers,
      })
      if (!res.ok) throw new Error('删除失败')
      setMessages(prev => prev.filter(m => m.id !== msgId))
      setHoverMsgId(null)
    } catch (e: any) {
      showToast(e.message || '删除失败')
    }
  }

  // 创建房间
  const createRoom = async () => {
    const name = prompt('房间名称:')
    if (!name) return
    const r = await fetch(`${API_BASE}/rooms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    const newRoom = await r.json()
    alert(`房间创建成功！Secret: ${newRoom.secret}\n请保存好，发送消息时需要用到。`)
    loadRooms()
  }

  const currentRoom = rooms.find(r => r.id === currentRoomId)

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
      if (isToday) return '今天'
      if (isYesterday) return '昨天'
      const pad = (n: number) => n.toString().padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    } catch { return '' }
  }

  // 缓存过滤后的消息，避免输入时重复计算
  const filteredMessages = useMemo(() => {
    if (!searchQuery.trim()) return messages
    const q = searchQuery.toLowerCase()
    return messages.filter((msg: Message) =>
      (msg.content || '').toLowerCase().includes(q) ||
      (msg.sender_name || '').toLowerCase().includes(q)
    )
  }, [messages, searchQuery])

  return (
    <div className="flex h-screen w-screen overflow-hidden"
         data-theme={theme}
         style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Mobile overlay */}
      {(showSidebar || showMembers) && (
        <div className="fixed inset-0 z-40 lg:hidden" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} onClick={() => { setShowSidebar(false); setShowMembers(false) }} />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 flex-shrink-0 flex flex-col transition-transform duration-300 lg:translate-x-0 ${showSidebar ? 'translate-x-0' : '-translate-x-full'}`}
              style={{ borderRadius: '0 24px 24px 0', backgroundColor: 'var(--bg-elevated)' }}>
        <div className="p-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-wide text-[#00d4aa]">🤖 Agent Coop</h2>
        </div>
        <div className="p-3">
          <button
            onClick={createRoom}
            className="w-full py-2 px-3 rounded-2xl text-xs font-medium transition-all hover:bg-white/10 liquid-glass"
          >
            + 创建房间
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
          {rooms.map(room => (
            <button
              key={room.id}
              onClick={() => setCurrentRoomId(room.id)}
              className={`w-full text-left px-3 py-2.5 rounded-2xl text-sm transition-all ${
                room.id === currentRoomId
                  ? 'text-[#00d4aa]'
                  : 'hover:bg-white/[0.05]'
              }`}
              style={room.id === currentRoomId ? { backgroundColor: 'rgba(0,212,170,0.12)' } : { color: 'var(--text-muted)' }}
            >
              <span className="font-medium">#</span> {room.name}
            </button>
          ))}
        </div>
        <div className="p-3">
          <div className="text-[10px] mb-1" style={{ color: 'var(--text-muted)' }}>你的名字</div>
          <input
            value={myName}
            onChange={e => setMyName(e.target.value)}
            className="w-full rounded-xl px-3 py-1.5 text-xs outline-none liquid-glass focus:border-[#00d4aa]/50 transition-all"
          />
        </div>
      </aside>

      {/* Main Chat */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-14 flex items-center px-3 lg:px-5 gap-2 liquid-glass"
                style={{ borderRadius: '0 0 20px 20px', margin: '0 12px', borderTop: 'none' }}>
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="lg:hidden p-2 rounded-lg hover:bg-[var(--bg-surface)]"
            style={{ color: 'var(--text-secondary)' }}
          >
            ☰
          </button>
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="text-lg hidden sm:inline">#</span>
            <span className="font-semibold truncate">{currentRoom?.name || '选择房间'}</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl transition-all hover:bg-white/10 liquid-glass"
              title={theme === 'dark' ? '切换亮色' : '切换暗色'}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button
              onClick={() => setShowMembers(!showMembers)}
              className="lg:hidden p-2 rounded-xl hover:bg-white/10 transition-all liquid-glass"
            >
              👥
            </button>
            <span className={`w-2 h-2 rounded-full ${
              wsStatus === 'open' ? 'bg-[#00d4aa]' : wsStatus === 'connecting' ? 'bg-yellow-400' : 'bg-red-400'
            }`} />
            <span className="hidden sm:inline" style={{ color: 'var(--text-muted)' }}>{wsStatus === 'open' ? '实时' : wsStatus}</span>
          </div>
        </header>

        {/* Search */}
        <div className="px-5 pt-3">
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="🔍 搜索消息..."
            className="w-full rounded-2xl px-4 py-2 text-sm outline-none transition-all placeholder-white/30 liquid-glass focus:border-[#00d4aa]/40"
          />
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center mt-20">
              <div className="text-4xl mb-3" style={{ opacity: 0.15 }}>💬</div>
              <div className="text-sm text-[#55556e]">暂无消息</div>
            </div>
          )}
          {(() => {
            const result: React.ReactNode[] = []
            let lastDate = ''
            filteredMessages.forEach((msg: Message) => {
              const isSystem = msg.msg_type === 'join' || msg.msg_type === 'leave' || msg.msg_type === 'system'
              const isMe = msg.sender_name === myName
              const currDate = fmtDate(msg.created_at)
              
              if (!isSystem && currDate !== lastDate) {
                result.push(
                  <div key={`date-${msg.id}`} className="flex justify-center my-3">
                    <span className="text-[10px] px-3 py-0.5 rounded-full" style={{ color: 'var(--text-muted)', backgroundColor: 'var(--bg-elevated)' }}>
                      {currDate}
                    </span>
                  </div>
                )
                lastDate = currDate
              }
              
              if (isSystem) {
                result.push(
                  <div key={msg.id} className="flex justify-center">
                    <span className="text-[11px] px-3 py-1 rounded-full liquid-glass" style={{ color: 'var(--text-secondary)' }}>
                      {msg.content}
                    </span>
                  </div>
                )
                return
              }
            const canEdit = isMe && msg.sender_name === myName
            const isEditing = editingId === msg.id
            result.push(
              <div
                key={msg.id}
                className={`flex ${isMe ? 'justify-end' : 'justify-start'} group relative`}
                onMouseEnter={() => canEdit && setHoverMsgId(msg.id)}
                onMouseLeave={() => setHoverMsgId(null)}
              >
                {/* 回复/编辑/删除按钮 */}
                {hoverMsgId === msg.id && !isEditing && (
                  <div className={`absolute ${isMe ? 'left-0 -translate-x-full mr-1' : 'right-0 translate-x-full ml-1'} top-1 flex gap-1`}>
                    <button
                      onClick={() => startReply(msg)}
                      className="p-1 rounded liquid-glass text-[10px] transition-colors hover:brightness-125"
                      title="回复"
                    >
                      ↩️
                    </button>
                    {canEdit && (
                      <>
                        <button
                          onClick={() => startEdit(msg)}
                          className="p-1 rounded liquid-glass text-[10px] transition-colors hover:brightness-125"
                          title="编辑"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => deleteMsg(msg.id)}
                          className="p-1 rounded liquid-glass text-[10px] transition-colors hover:bg-red-500/30"
                          title="删除"
                        >
                          🗑️
                        </button>
                      </>
                    )}
                  </div>
                )}
                <div className={`max-w-[85%] sm:max-w-[70%] px-4 py-2.5 text-sm leading-relaxed ${
                  isMe
                    ? 'bg-gradient-to-br from-[#00d4aa] to-[#00a884] text-black rounded-br-3xl rounded-tl-3xl rounded-tr-3xl shadow-[#00d4aa]/10'
                    : 'rounded-bl-3xl rounded-tr-3xl rounded-br-3xl liquid-glass'
                }`}>
                  {!isMe && (
                    <div className="text-[11px] font-semibold mb-0.5" style={{ color: '#8888cc' }}>
                      {msg.sender_name}
                      {msg.to_name && <span className="font-normal" style={{ color: 'var(--text-muted)' }}> → @{msg.to_name}</span>}
                    </div>
                  )}
                  {isEditing ? (
                    <div className="flex flex-col gap-2">
                      <textarea
                        value={editContent}
                        onChange={e => setEditContent(e.target.value)}
                        className="w-full border rounded-lg px-3 py-2 text-sm outline-none focus:border-[#00d4aa] resize-none"
                        style={{ backgroundColor: 'var(--bg-primary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                        rows={3}
                        autoFocus
                      />
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => { setEditingId(null); setEditContent('') }}
                          className="px-3 py-1 rounded-lg text-xs transition-colors"
                          style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--text-secondary)' }}
                        >
                          取消
                        </button>
                        <button
                          onClick={saveEdit}
                          className="px-3 py-1 rounded-lg bg-[#00d4aa] text-black text-xs font-semibold hover:opacity-90 transition-opacity"
                        >
                          保存
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="markdown-body">
                      <MemoizedMarkdown content={msg.content} />
                    </div>
                  )}
                  <div className={`text-[10px] mt-1 text-right ${isMe ? 'text-[#005a3d]' : 'text-[#555]'}`}>
                    {fmtTime(msg.created_at)}
                  </div>
                </div>
              </div>
            )
            })
            return result
          })()}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="px-5 pb-5 pt-2">
          {/* @快捷栏 */}
          <div className="flex items-center gap-1.5 mb-2 overflow-x-auto scrollbar-hide">
            <button
              onClick={() => insertMention('all')}
              className="shrink-0 px-3 py-1 rounded-full text-[11px] text-[#00d4aa] transition-all hover:bg-[#00d4aa]/20"
              style={{ backgroundColor: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: '9999px' }}
            >
              @所有人
            </button>
            {members
              .filter(m => m.name !== myName)
              .map(m => (
                <button
                  key={m.id}
                  onClick={() => insertMention(m.name)}
                  className="shrink-0 px-3 py-1 rounded-full text-[11px] transition-all hover:bg-white/10"
                  style={{ color: 'var(--text-muted)', backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '9999px' }}
                >
                  @{m.name}
                </button>
              ))}
          </div>
          {/* 回复引用 */}
          {replyTo && (
            <div className="flex items-center gap-2 mb-2 px-3 py-2 rounded-2xl liquid-glass">
              <div className="flex-1 min-w-0">
                <div className="text-[10px] mb-0.5" style={{ color: 'var(--text-secondary)' }}>回复 {replyTo.sender_name}</div>
                <div className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>{replyTo.content}</div>
              </div>
              <button
                onClick={cancelReply}
                className="p-1 rounded-lg hover:bg-white/10 transition-colors"
                style={{ color: 'var(--text-muted)' }}
              >
                ✕
              </button>
            </div>
          )}
          <div className="flex gap-2 rounded-3xl px-4 py-2 transition-all liquid-glass-strong focus-within:border-[#00d4aa]/40">
            <textarea
              ref={inputRef as any}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key !== 'Enter') return
                if (e.shiftKey) {
                  e.preventDefault()
                  setInput(prev => prev + '\n')
                  return
                }
                if (e.nativeEvent.isComposing || e.keyCode === 229) return
                e.preventDefault()
                sendMessage()
              }}
              rows={1}
              placeholder={replyTo ? `回复 ${replyTo.sender_name}...` : `以 ${myName} 的身份发消息...`}
              className="flex-1 bg-transparent outline-none text-sm resize-none overflow-y-auto max-h-32 py-1"
              style={{ color: 'var(--text-primary)' }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isSending}
              className="px-4 py-1.5 rounded-xl bg-[#00d4aa] text-black text-xs font-semibold hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed transition-opacity flex items-center gap-1"
            >
              {isSending && (
                <svg className="animate-spin h-3 w-3 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
              {isSending ? '发送中...' : '发送'}
            </button>
          </div>
        </div>
      </main>

      {/* Member List */}
      <aside className={`fixed lg:static inset-y-0 right-0 z-50 w-52 flex-shrink-0 flex flex-col transition-transform duration-300 lg:translate-x-0 ${showMembers ? 'translate-x-0' : 'translate-x-full'}`}
              style={{ borderRadius: '24px 0 0 24px', backgroundColor: 'var(--bg-elevated)' }}>
        <div className="p-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          成员 — {members.length}
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {members.map(m => {
            const status = agentStatus[m.name]
            let statusColor = 'bg-[var(--status-offline)]'
            let statusText = '离线'
            if (status) {
              if (status.process_online && status.listening) {
                statusColor = 'bg-[#00d4aa]'
                statusText = '在线'
              } else if (status.process_online) {
                statusColor = 'bg-yellow-400'
                statusText = '进程中'
              }
            }
            return (
              <div key={m.id} className="flex items-center gap-2 px-2 py-1.5 rounded-2xl transition-colors hover:bg-white/[0.05]">
                <div className={`w-2 h-2 rounded-full ${statusColor}`} title={statusText} />
                <div className="flex flex-col min-w-0">
                  <span className="text-sm truncate">{m.name}</span>
                  {status && (
                    <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                      {status.process_online ? (status.listening ? '监听中' : '未监听') : '离线'}
                    </span>
                  )}
                </div>
                <span className="text-[10px] ml-auto" style={{ color: 'var(--text-muted)' }}>{m.type}</span>
              </div>
            )
          })}
        </div>
      </aside>

      {/* Toast 通知 */}
      {toast && (
        <div className={`fixed top-4 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg text-sm font-medium shadow-2xl ${
          toast.type === 'error' ? 'bg-red-500/90 text-white' : 'bg-[#00d4aa]/90 text-black'
        }`}
             style={{ animation: 'slideDown 0.3s ease-out' }}>
          {toast.message}
        </div>
      )}
    </div>
  )
}
