export interface Room {
  id: number
  name: string
  secret: string
  created_at: string
}

export interface Member {
  id: number
  name: string
  type: string
  last_active: string
}

export interface Message {
  id: number
  room_id: number
  sender_name: string | null
  content: string
  to_name: string | null
  msg_type: string
  created_at: string
}

export interface AgentStatus {
  process_online: boolean
  listening: boolean
  last_active: string
}
