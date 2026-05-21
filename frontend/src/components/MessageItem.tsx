import { useState } from 'react'
import type { Message } from '../types'
import { MemoizedMarkdown } from './MarkdownRenderer'

interface MessageItemProps {
  msg: Message
  isMe: boolean
  myName: string
  editingId: number | null
  onStartEdit: (msg: Message) => void
  onSaveEdit: (msgId: number, content: string) => void
  onCancelEdit: () => void
  onDelete: (msgId: number) => void
  onReply: (msg: Message) => void
  fmtTime: (iso: string) => string
}

export default function MessageItem({
  msg,
  isMe,
  myName,
  editingId,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDelete,
  onReply,
  fmtTime,
}: MessageItemProps) {
  const [hover, setHover] = useState(false)
  const [editContent, setEditContent] = useState(msg.content)
  const isEditing = editingId === msg.id
  const canEdit = isMe && msg.sender_name === myName

  const isSystem = msg.msg_type === 'join' || msg.msg_type === 'leave' || msg.msg_type === 'system'

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span
          className="text-[11px] px-3 py-1 rounded-full liquid-glass"
          style={{ color: 'var(--text-secondary)' }}
        >
          {msg.content}
        </span>
      </div>
    )
  }

  return (
    <div
      className={`flex ${isMe ? 'justify-end' : 'justify-start'} group relative`}
      onMouseEnter={() => canEdit && setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {hover && !isEditing && (
        <div
          className={`absolute ${isMe ? 'left-0 -translate-x-full mr-1' : 'right-0 translate-x-full ml-1'} top-1 flex gap-1`}
        >
          <button
            onClick={() => onReply(msg)}
            className="p-1 rounded liquid-glass text-[10px] transition-colors hover:brightness-125"
            title="Reply"
          >
            ↩️
          </button>
          {canEdit && (
            <>
              <button
                onClick={() => { setEditContent(msg.content); onStartEdit(msg) }}
                className="p-1 rounded liquid-glass text-[10px] transition-colors hover:brightness-125"
                title="Edit"
              >
                ✏️
              </button>
              <button
                onClick={() => onDelete(msg.id)}
                className="p-1 rounded liquid-glass text-[10px] transition-colors hover:bg-red-500/30"
                title="Delete"
              >
                🗑️
              </button>
            </>
          )}
        </div>
      )}
      <div
        className={`max-w-[85%] sm:max-w-[70%] px-4 py-2.5 text-sm leading-relaxed ${
          isMe
            ? 'bg-gradient-to-br from-[#00d4aa] to-[#00a884] text-black rounded-br-3xl rounded-tl-3xl rounded-tr-3xl shadow-[#00d4aa]/10'
            : 'rounded-bl-3xl rounded-tr-3xl rounded-br-3xl liquid-glass'
        }`}
      >
        {!isMe && (
          <div className="text-[11px] font-semibold mb-0.5" style={{ color: '#8888cc' }}>
            {msg.sender_name}
            {msg.to_name && (
              <span className="font-normal" style={{ color: 'var(--text-muted)' }}>
                {' '}
                → @{msg.to_name}
              </span>
            )}
          </div>
        )}
        {isEditing ? (
          <div className="flex flex-col gap-2">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm outline-none focus:border-[#00d4aa] resize-none"
              style={{
                backgroundColor: 'var(--bg-primary)',
                borderColor: 'var(--border-color)',
                color: 'var(--text-primary)',
              }}
              rows={3}
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={onCancelEdit}
                className="px-3 py-1 rounded-lg text-xs transition-colors"
                style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--text-secondary)' }}
              >
                Cancel
              </button>
              <button
                onClick={() => onSaveEdit(msg.id, editContent)}
                className="px-3 py-1 rounded-lg bg-[#00d4aa] text-black text-xs font-semibold hover:opacity-90 transition-opacity"
              >
                Save
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
}
