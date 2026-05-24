import { describe, it, expect } from 'vitest'
import { getSenderColor } from '../components/MessageItem'

describe('getSenderColor', () => {
  it('returns blue for human', () => {
    expect(getSenderColor('human')).toBe('var(--accent-blue)')
  })

  it('returns purple for claude-agent', () => {
    expect(getSenderColor('claude-agent')).toBe('var(--accent-purple)')
  })

  it('returns teal for Kimi-Agent', () => {
    expect(getSenderColor('Kimi-Agent')).toBe('var(--accent-teal)')
  })

  it('returns teal for kimi-agent (lowercase)', () => {
    expect(getSenderColor('kimi-agent')).toBe('var(--accent-teal)')
  })

  it('returns system color for system', () => {
    expect(getSenderColor('system')).toBe('var(--sender-system)')
  })

  it('returns default coral for unknown sender', () => {
    expect(getSenderColor('unknown-agent')).toBe('var(--accent-coral)')
  })

  it('returns default coral for null', () => {
    expect(getSenderColor(null)).toBe('var(--accent-coral)')
  })
})
