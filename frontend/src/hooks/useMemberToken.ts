import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'agent-coop-member-tokens'

interface MemberTokenEntry {
  name: string
  token: string
}

interface MemberTokens {
  [roomId: number]: MemberTokenEntry
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

export function useMemberToken(roomId: number | null) {
  const [token, setToken] = useState<string>('')
  const [memberName, setMemberName] = useState<string>('')

  // Load token from storage or cookie when roomId changes
  useEffect(() => {
    if (!roomId) {
      setToken('')
      setMemberName('')
      return
    }
    try {
      // Prefer localStorage (has name + token)
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const data: MemberTokens = JSON.parse(saved)
        const entry = data[roomId]
        if (entry?.token) {
          setToken(entry.token)
          setMemberName(entry.name)
          return
        }
      }
      // Fallback to cookie (token only, no name)
      const cookieToken = getCookie('member_token')
      if (cookieToken) {
        setToken(cookieToken)
        // Name unknown from cookie alone; will be resolved later if needed
        setMemberName('')
        return
      }
    } catch {}
    setToken('')
    setMemberName('')
  }, [roomId])

  const saveToken = useCallback((newRoomId: number, name: string, newToken: string) => {
    const saved = localStorage.getItem(STORAGE_KEY)
    const data: MemberTokens = saved ? JSON.parse(saved) : {}
    data[newRoomId] = { name, token: newToken }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    setToken(newToken)
    setMemberName(name)
  }, [])

  const clearToken = useCallback(() => {
    if (!roomId) return
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const data: MemberTokens = JSON.parse(saved)
      delete data[roomId]
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    }
    setToken('')
    setMemberName('')
  }, [roomId])

  return { token, memberName, saveToken, clearToken }
}
