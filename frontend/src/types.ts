export interface Room {
  id: number;
  name: string;
  secret: string;
  announcement?: string;
  created_at: string;
}

export interface Member {
  id: number;
  name: string;
  type: string;
  last_active: string;
  role?: string;
  description?: string;
  is_me?: boolean;
}

export interface MemberStats {
  member_id: number;
  name: string;
  type: string;
  role: string;
  description: string;
  message_count: number;
  last_message_at: string | null;
}

export interface Attachment {
  id: number;
  filename: string;
  mime_type: string;
  size: number;
  url: string;
}

export interface Message {
  id: number;
  room_id: number;
  sender_name: string | null;
  content: string;
  to_name: string | null;
  msg_type: string;
  created_at: string;
  updated_at?: string | null;
  attachments?: Attachment[];
}

export interface AgentStatus {
  process_online: boolean;
  listening: boolean;
  last_active: string;
  type: string;
}
