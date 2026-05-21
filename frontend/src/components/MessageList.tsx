import { useRef, useEffect, useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { Message } from '../types'
import MessageItem from './MessageItem'

interface VirtualItem {
  type: 'date' | 'message'
  id: string
  date?: string
  msg?: Message
}

interface MessageListProps {
  messages: Message[]
  filteredMessages: Message[]
  myName: string
  editingId: number | null
  onStartEdit: (msg: Message) => void
  onSaveEdit: (msgId: number, content: string) => void
  onCancelEdit: () => void
  onDelete: (msgId: number) => void
  onReply: (msg: Message) => void
  fmtTime: (iso: string) => string
  fmtDate: (iso: string) => string
}

export default function MessageList({
  messages,
  filteredMessages,
  myName,
  editingId,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDelete,
  onReply,
  fmtTime,
  fmtDate,
}: MessageListProps) {
  const parentRef = useRef<HTMLDivElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const prevMsgCount = useRef(0)

  // 构建虚拟化项（消息 + 日期分隔符）
  const virtualItems = useMemo(() => {
    const items: VirtualItem[] = []
    let lastDate = ''
    for (const msg of filteredMessages) {
      const isSystem = msg.msg_type === 'join' || msg.msg_type === 'leave' || msg.msg_type === 'system'
      const currDate = fmtDate(msg.created_at)

      if (isSystem) {
        items.push({ type: 'message', id: `sys-${msg.id}`, msg })
        continue
      }

      if (currDate !== lastDate) {
        items.push({ type: 'date', id: `date-${msg.id}`, date: currDate })
        lastDate = currDate
      }

      items.push({ type: 'message', id: `msg-${msg.id}`, msg })
    }
    return items
  }, [filteredMessages, fmtDate])

  const virtualizer = useVirtualizer({
    count: virtualItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    measureElement: (el) => el.getBoundingClientRect().height,
    overscan: 5,
  })

  // 新消息自动滚动到底部
  useEffect(() => {
    if (messages.length > prevMsgCount.current) {
      virtualizer.scrollToIndex(virtualItems.length - 1, { align: 'end', behavior: 'smooth' })
    }
    prevMsgCount.current = messages.length
  }, [messages.length, virtualItems.length, virtualizer])

  return (
    <div ref={parentRef} className="flex-1 overflow-y-auto relative">
      {messages.length === 0 && (
        <div className="text-center mt-20">
          <div className="text-4xl mb-3" style={{ opacity: 0.15 }}>
            💬
          </div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            No messages yet
          </div>
        </div>
      )}
      {messages.length > 0 && (
        <div
          className="py-4"
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            position: 'relative',
            width: '100%',
          }}
        >
          {virtualizer.getVirtualItems().map((virtualItem) => {
            const item = virtualItems[virtualItem.index]
            return (
              <div
                key={item.id}
                ref={virtualizer.measureElement}
                data-index={virtualItem.index}
                className="px-5"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`,
                  paddingBottom: '12px',
                }}
              >
                {item.type === 'date' && (
                  <div className="flex justify-center my-3">
                    <span
                      className="text-[10px] px-3 py-0.5 rounded-full"
                      style={{
                        color: 'var(--text-muted)',
                        backgroundColor: 'var(--bg-elevated)',
                      }}
                    >
                      {item.date}
                    </span>
                  </div>
                )}
                {item.type === 'message' && item.msg && (
                  <MessageItem
                    msg={item.msg}
                    isMe={item.msg.sender_name === myName}
                    myName={myName}
                    editingId={editingId}
                    onStartEdit={onStartEdit}
                    onSaveEdit={onSaveEdit}
                    onCancelEdit={onCancelEdit}
                    onDelete={onDelete}
                    onReply={onReply}
                    fmtTime={fmtTime}
                  />
                )}
              </div>
            )
          })}
        </div>
      )}
      <div ref={chatEndRef} style={{ height: 1 }} />
    </div>
  )
}
