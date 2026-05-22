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
  role?: string
  description?: string
}

export interface MemberStats {
  member_id: number
  name: string
  type: string
  role: string
  description: string
  message_count: number
  last_message_at: string | null
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
  type: string
}
