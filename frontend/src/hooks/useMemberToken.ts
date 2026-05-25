import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'agentroom-member-tokens'
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
      // Fallback to cookie (token + name)
      const cookieToken = getCookie('member_token')
      const cookieName = getCookie('member_name')
      if (cookieToken) {
        setToken(cookieToken)
        setMemberName(cookieName || '')
        // Save to localStorage for next time
        if (cookieName) {
          const data: MemberTokens = saved ? JSON.parse(saved) : {}
          data[roomId] = { name: cookieName, token: cookieToken }
          localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
        }
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
