import { useRef } from 'react'
import type { Member, Message } from '../types'

interface MessageInputProps {
  input: string
  onInputChange: (v: string) => void
  onSend: () => void
  isSending: boolean
  myName: string
  members: Member[]
  replyTo: Message | null
  onCancelReply: () => void
  onInsertMention: (name: string) => void
}

export default function MessageInput({
  input,
  onInputChange,
  onSend,
  isSending,
  myName,
  members,
  replyTo,
  onCancelReply,
  onInsertMention,
}: MessageInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null)

  return (
    <div className="px-5 pb-5 pt-2">
      {/* Mention shortcuts */}
      <div className="flex items-center gap-1.5 mb-2 overflow-x-auto scrollbar-hide">
        <button
          onClick={() => onInsertMention('all')}
          className="shrink-0 px-3 py-1 rounded-full text-[11px] text-[#00d4aa] transition-all hover:bg-[#00d4aa]/20"
          style={{
            backgroundColor: 'rgba(0,212,170,0.1)',
            border: '1px solid rgba(0,212,170,0.2)',
            borderRadius: '9999px',
          }}
        >
          @all
        </button>
        {members
          .filter((m) => m.name !== myName)
          .map((m) => (
            <button
              key={m.id}
              onClick={() => onInsertMention(m.name)}
              className="shrink-0 px-3 py-1 rounded-full text-[11px] transition-all hover:bg-white/10"
              style={{
                color: 'var(--text-muted)',
                backgroundColor: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '9999px',
              }}
            >
              @{m.name}
            </button>
          ))}
      </div>

      {/* Reply quote */}
      {replyTo && (
        <div className="flex items-center gap-2 mb-2 px-3 py-2 rounded-2xl liquid-glass">
          <div className="flex-1 min-w-0">
            <div className="text-[10px] mb-0.5" style={{ color: 'var(--text-secondary)' }}>
              Reply to {replyTo.sender_name}
            </div>
            <div className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>
              {replyTo.content}
            </div>
          </div>
          <button
            onClick={onCancelReply}
            className="p-1 rounded-lg hover:bg-white/10 transition-colors"
            style={{ color: 'var(--text-muted)' }}
          >
            ✕
          </button>
        </div>
      )}

      <div className="flex gap-2 rounded-3xl px-4 py-2 transition-all liquid-glass-strong focus-within:border-[#00d4aa]/40">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key !== 'Enter') return
            if (e.shiftKey) {
              e.preventDefault()
              onInputChange(input + '\n')
              return
            }
            if (e.nativeEvent.isComposing || e.keyCode === 229) return
            e.preventDefault()
            onSend()
          }}
          rows={1}
          placeholder={
            replyTo ? `Reply to ${replyTo.sender_name}...` : `Message as ${myName}...`
          }
          className="flex-1 bg-transparent outline-none text-sm resize-none overflow-y-auto max-h-32 py-1"
          style={{ color: 'var(--text-primary)' }}
        />
        <button
          onClick={onSend}
          disabled={!input.trim() || isSending}
          className="px-4 py-1.5 rounded-xl bg-[#00d4aa] text-black text-xs font-semibold hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed transition-opacity flex items-center gap-1"
        >
          {isSending ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
