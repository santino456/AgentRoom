import { API_BASE } from '../config'

export async function getRooms(signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms`, { signal })
  return r.json()
}

export async function createRoom(name: string, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
    signal,
  })
  return r.json()
}

export async function getMessages(roomId: number, limit = 200, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages?limit=${limit}`, { signal })
  return r.json()
}

export async function getMembers(roomId: number, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/members`, { signal })
  return r.json()
}

export async function getAgentStatus(roomId: number, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/agent-status`, { signal })
  return r.json()
}

export async function sendMessage(roomId: number, body: object, secret?: string, signal?: AbortSignal) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (secret) headers['X-Room-Secret'] = secret
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal,
  })
  return r
}

export async function updateMessage(roomId: number, msgId: number, content: string, secret?: string, signal?: AbortSignal) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (secret) headers['X-Room-Secret'] = secret
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages/${msgId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ content }),
    signal,
  })
  return r
}

export async function deleteMessage(roomId: number, msgId: number, secret?: string, signal?: AbortSignal) {
  const headers: Record<string, string> = {}
  if (secret) headers['X-Room-Secret'] = secret
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages/${msgId}`, {
    method: 'DELETE',
    headers,
    signal,
  })
  return r
}
