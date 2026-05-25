import React, { useState, useMemo } from "react";
import type { Message, Member } from "../types";
import { MemoizedMarkdown } from "./MarkdownRenderer";
import Lightbox from "./Lightbox";

interface MessageItemProps {
  msg: Message;
  isMe: boolean;
  myName: string;
  members: Member[];
  editingId: number | null;
  onStartEdit: (msg: Message) => void;
  onSaveEdit: (msgId: number, content: string) => void;
  onCancelEdit: () => void;
  onDelete: (msgId: number) => void;
  fmtTime: (iso: string) => string;
}

// Get sender color based on name - richer palette
export function getSenderColor(name: string | null): string {
  if (!name) return "var(--accent-coral)";
  const colors: Record<string, string> = {
    human: "var(--accent-blue)",
    "claude-agent": "var(--accent-purple)",
    "Kimi-Agent": "var(--accent-teal)",
    "kimi-agent": "var(--accent-teal)",
    system: "var(--sender-system)",
  };
  return colors[name] || "var(--accent-coral)";
}

// Get message background gradient for "me" messages - uses CSS variable
function getMeGradient(name: string | null): string {
  if (!name) return "var(--msg-me-gradient)";
  const gradients: Record<string, string> = {
    human: "var(--msg-me-gradient)",
    "claude-agent":
      "linear-gradient(135deg, var(--accent-purple), var(--accent-secondary))",
    "Kimi-Agent":
      "linear-gradient(135deg, var(--accent-teal), var(--accent-cyan))",
    "kimi-agent":
      "linear-gradient(135deg, var(--accent-teal), var(--accent-cyan))",
  };
  return gradients[name] || "var(--msg-me-gradient)";
}

function MessageItem({
  msg,
  isMe,
  myName,
  members,
  editingId,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDelete,
  fmtTime,
}: MessageItemProps) {
  void members;
  const [hover, setHover] = useState(false);
  const [editContent, setEditContent] = useState(msg.content);
  const [lightbox, setLightbox] = useState<{
    src: string;
    alt?: string;
  } | null>(null);
  const isEditing = editingId === msg.id;
  const canEdit = isMe && msg.sender_name === myName;

  const senderColor = useMemo(
    () => getSenderColor(msg.sender_name),
    [msg.sender_name],
  );
  const meGradient = useMemo(
    () => getMeGradient(msg.sender_name),
    [msg.sender_name],
  );

  const displayName = msg.sender_name || "Unknown";

  const isSystem =
    msg.msg_type === "join" ||
    msg.msg_type === "leave" ||
    msg.msg_type === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center message-appear">
        <span
          className="text-[11px] px-4 py-1.5 rounded-full"
          style={{
            color: "var(--text-muted)",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-color)",
          }}
        >
          {msg.content}
        </span>
      </div>
    );
  }

  return (
    <div
      className={`flex ${isMe ? "justify-end" : "justify-start"} group relative message-appear`}
      onMouseEnter={() => canEdit && setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {hover && !isEditing && (
        <div
          className={`absolute ${isMe ? "left-0 -translate-x-full mr-1" : "right-0 translate-x-full ml-1"} top-1 flex gap-1`}
        >
          {canEdit && (
            <>
              <button
                onClick={() => {
                  setEditContent(msg.content);
                  onStartEdit(msg);
                }}
                className="p-1.5 rounded-lg text-[10px] transition-all btn-press hover:brightness-125"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  color: "var(--text-secondary)",
                }}
                title="Edit"
              >
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                </svg>
              </button>
              <button
                onClick={() => onDelete(msg.id)}
                className="p-1.5 rounded-lg text-[10px] transition-all btn-press hover:bg-red-500/20"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  color: "var(--accent-coral)",
                }}
                title="Delete"
              >
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M3 6h18" />
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                </svg>
              </button>
            </>
          )}
        </div>
      )}
      <div
        className={`max-w-[85%] sm:max-w-[70%] px-4 py-2.5 text-sm leading-relaxed ${
          isMe
            ? "text-white rounded-2xl rounded-br-md shadow-lg"
            : "rounded-2xl rounded-bl-md"
        }`}
        style={
          isMe
            ? { background: meGradient }
            : {
                backgroundColor: "var(--msg-other-bg)",
                border: "1px solid var(--border-color)",
              }
        }
      >
        {!isMe && (
          <div
            className="text-[11px] font-semibold mb-1 flex items-center gap-1.5"
            style={{ color: senderColor }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: senderColor }}
            />
            {displayName}
            {msg.to_name && (
              <span
                className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium"
                style={{
                  backgroundColor: "rgba(16, 185, 129, 0.15)",
                  color: "#10b981",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                }}
              >
                <svg
                  width="8"
                  height="8"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                  <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
                </svg>
                @{msg.to_name}
              </span>
            )}
          </div>
        )}
        {isMe && msg.to_name && (
          <div className="text-[11px] mb-1 flex items-center gap-1.5 justify-end">
            <span
              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium"
              style={{
                backgroundColor: "rgba(16, 185, 129, 0.2)",
                color: "#6ee7b7",
                border: "1px solid rgba(16, 185, 129, 0.3)",
              }}
            >
              <svg
                width="8"
                height="8"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
              </svg>
              @{msg.to_name}
            </span>
          </div>
        )}
        {isEditing ? (
          <div className="flex flex-col gap-2">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full rounded-xl px-3 py-2 text-sm outline-none resize-none"
              style={{
                backgroundColor: "rgba(0,0,0,0.2)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#fff",
              }}
              rows={3}
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={onCancelEdit}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all btn-press"
                style={{
                  backgroundColor: "rgba(255,255,255,0.15)",
                  color: "rgba(255,255,255,0.8)",
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => onSaveEdit(msg.id, editContent)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all btn-press hover:brightness-110"
                style={{
                  backgroundColor: "#fff",
                  color: "#1d1d1f",
                }}
              >
                Save
              </button>
            </div>
          </div>
        ) : (
          <div className="markdown-body">
            <MemoizedMarkdown
              content={msg.content}
              onImageClick={(src, alt) => setLightbox({ src, alt })}
            />
          </div>
        )}
        <div
          className={`text-[10px] mt-1 text-right ${isMe ? "text-white/60" : "text-[#555]"}`}
        >
          {fmtTime(msg.created_at)}
        </div>
      </div>
      {lightbox && (
        <Lightbox
          src={lightbox.src}
          alt={lightbox.alt}
          onClose={() => setLightbox(null)}
        />
      )}
    </div>
  );
}

export default React.memo(MessageItem);
