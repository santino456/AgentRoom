import { useRef, useEffect } from 'react'
import type { Message } from '../types'
import MessageItem from './MessageItem'

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
  const chatEndRef = useRef<HTMLDivElement>(null)
  const prevMsgCount = useRef(0)

  useEffect(() => {
    if (messages.length > prevMsgCount.current) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    prevMsgCount.current = messages.length
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
      {messages.length === 0 && (
        <div className="text-center mt-20">
          <div className="text-4xl mb-3" style={{ opacity: 0.15 }}>
            💬
          </div>
          <div className="text-sm text-[#55556e]">No messages yet</div>
        </div>
      )}
      {(() => {
        const result: React.ReactNode[] = []
        let lastDate = ''
        filteredMessages.forEach((msg: Message) => {
          const isSystem =
            msg.msg_type === 'join' || msg.msg_type === 'leave' || msg.msg_type === 'system'
          const isMe = msg.sender_name === myName
          const currDate = fmtDate(msg.created_at)

          if (!isSystem && currDate !== lastDate) {
            result.push(
              <div key={`date-${msg.id}`} className="flex justify-center my-3">
                <span
                  className="text-[10px] px-3 py-0.5 rounded-full"
                  style={{
                    color: 'var(--text-muted)',
                    backgroundColor: 'var(--bg-elevated)',
                  }}
                >
                  {currDate}
                </span>
              </div>
            )
            lastDate = currDate
          }

          result.push(
            <MessageItem
              key={msg.id}
              msg={msg}
              isMe={isMe}
              myName={myName}
              editingId={editingId}
              onStartEdit={onStartEdit}
              onSaveEdit={onSaveEdit}
              onCancelEdit={onCancelEdit}
              onDelete={onDelete}
              onReply={onReply}
              fmtTime={fmtTime}
            />
          )
        })
        return result
      })()}
      <div ref={chatEndRef} />
    </div>
  )
}
