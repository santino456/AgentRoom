import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

// Minimal MessageItem-like component for testing
function TestMessageItem({
  message,
  isMe,
  isSystem,
}: {
  message: { id: number; sender_name: string; content: string; msg_type: string; created_at: string }
  isMe: boolean
  isSystem: boolean
}) {
  if (isSystem) {
    return (
      <div data-testid="system-msg">
        <span>{message.content}</span>
      </div>
    )
  }
  return (
    <div data-testid="msg-item">
      <span data-testid="sender">{message.sender_name}</span>
      <span data-testid="content">{message.content}</span>
      {isMe && <span data-testid="me-badge">me</span>}
    </div>
  )
}

describe('MessageItem', () => {
  it('renders system message', () => {
    const msg = {
      id: 1,
      sender_name: 'system',
      content: '@alice joined the room.',
      msg_type: 'join',
      created_at: '2026-05-21T10:00:00',
    }
    render(<TestMessageItem message={msg} isMe={false} isSystem={true} />)
    expect(screen.getByTestId('system-msg')).toHaveTextContent('@alice joined the room.')
  })

  it('renders user message with sender name', () => {
    const msg = {
      id: 2,
      sender_name: 'bob',
      content: 'hello world',
      msg_type: 'message',
      created_at: '2026-05-21T10:05:00',
    }
    render(<TestMessageItem message={msg} isMe={false} isSystem={false} />)
    expect(screen.getByTestId('sender')).toHaveTextContent('bob')
    expect(screen.getByTestId('content')).toHaveTextContent('hello world')
    expect(screen.queryByTestId('me-badge')).not.toBeInTheDocument()
  })

  it('renders my message with badge', () => {
    const msg = {
      id: 3,
      sender_name: 'alice',
      content: 'my message',
      msg_type: 'message',
      created_at: '2026-05-21T10:10:00',
    }
    render(<TestMessageItem message={msg} isMe={true} isSystem={false} />)
    expect(screen.getByTestId('me-badge')).toBeInTheDocument()
  })
})
