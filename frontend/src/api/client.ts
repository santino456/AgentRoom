import { API_BASE } from '../config'

export async function getRooms(signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms`, { signal, credentials: 'include' })
  return r.json()
}

export async function createRoom(name: string, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
    signal,
    credentials: 'include',
  })
  return r.json()
}

export async function getMessages(roomId: number, limit = 200, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages?limit=${limit}`, { signal, credentials: 'include' })
  return r.json()
}

export async function getMembers(roomId: number, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/members`, { signal, credentials: 'include' })
  return r.json()
}

export async function getAgentStatus(roomId: number, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/agent-status`, { signal, credentials: 'include' })
  return r.json()
}

export async function sendMessage(roomId: number, body: object, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
    credentials: 'include',
  })
  return r
}

export async function updateMessage(roomId: number, msgId: number, content: string, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages/${msgId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
    signal,
    credentials: 'include',
  })
  return r
}

export async function deleteMessage(roomId: number, msgId: number, signal?: AbortSignal) {
  const r = await fetch(`${API_BASE}/rooms/${roomId}/messages/${msgId}`, {
    method: 'DELETE',
    signal,
    credentials: 'include',
  })
  return r
}
