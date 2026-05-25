import { useRef, useState, useCallback, useEffect } from "react";
import type { Member } from "../types";

interface MessageInputProps {
  input: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  isSending: boolean;
  myName: string;
  members: Member[];
  onInsertMention: (name: string) => void;
  onUploadFiles?: (files: FileList) => Promise<void>;
  isUploading?: boolean;
  uploadProgress?: string;
}

export default function MessageInput({
  input,
  onInputChange,
  onSend,
  isSending,
  myName,
  members,
  onInsertMention,
  onUploadFiles,
  isUploading,
  uploadProgress,
}: MessageInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Auto-resize textarea
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 128) + "px";
  }, [input]);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0 || !onUploadFiles) return;
      await onUploadFiles(files);
    },
    [onUploadFiles],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const disabled = isSending || isUploading;

  return (
    <div
      className="px-5 pb-5 pt-2"
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
    >
      {/* Mention shortcuts */}
      <div className="flex items-center gap-1.5 mb-2 overflow-x-auto scrollbar-hide">
        <button
          onClick={() => onInsertMention("all")}
          className="shrink-0 px-3 py-1 rounded-full text-[11px] text-[#00d4aa] transition-all hover:bg-[#00d4aa]/20"
          style={{
            backgroundColor: "rgba(0,212,170,0.1)",
            border: "1px solid rgba(0,212,170,0.2)",
            borderRadius: "9999px",
          }}
        >
          @all
        </button>
        {members
          .filter((m) => m.name !== myName)
          .map((m) => (
            <button
              key={m.id}
              onClick={() => onInsertMention(m.name)}
              className="shrink-0 px-3 py-1 rounded-full text-[11px] transition-all hover:bg-white/10"
              style={{
                color: "var(--text-muted)",
                backgroundColor: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "9999px",
              }}
            >
              @{m.name}
            </button>
          ))}
      </div>

      {/* Drag overlay */}
      {isDragOver && (
        <div className="mb-2 px-4 py-3 rounded-2xl border-2 border-dashed border-[#00d4aa]/60 text-center text-sm text-[#00d4aa] bg-[#00d4aa]/5">
          Drop files here to upload
        </div>
      )}

      {/* Upload progress */}
      {isUploading && uploadProgress && (
        <div
          className="mb-2 px-3 py-1.5 rounded-xl text-xs"
          style={{
            color: "var(--text-secondary)",
            backgroundColor: "rgba(0,212,170,0.08)",
          }}
        >
          📎 {uploadProgress}
        </div>
      )}

      <div
        className="flex items-end gap-2 rounded-3xl px-4 py-2 transition-all liquid-glass-strong"
        style={{
          border: isDragOver
            ? "1px solid rgba(0,212,170,0.5)"
            : "1px solid transparent",
        }}
      >
        {/* Attach button */}
        {onUploadFiles && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              className="p-2 rounded-xl hover:bg-white/10 disabled:opacity-30 transition-colors shrink-0"
              style={{ color: "var(--text-muted)" }}
              title="Attach file"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
          </>
        )}

        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key !== "Enter") return;
            if (e.shiftKey) {
              e.preventDefault();
              onInputChange(input + "\n");
              return;
            }
            if (e.nativeEvent.isComposing || e.keyCode === 229) return;
            e.preventDefault();
            onSend();
          }}
          rows={1}
          placeholder={`Message as ${myName}...`}
          className="flex-1 bg-transparent outline-none text-sm resize-none overflow-y-auto max-h-32 py-1"
          style={{ color: "var(--text-primary)" }}
        />
        <button
          onClick={onSend}
          disabled={!input.trim() || disabled}
          className="px-4 py-1.5 rounded-xl bg-[#00d4aa] text-black text-xs font-semibold hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed transition-opacity flex items-center gap-1 shrink-0"
        >
          {isSending ? "Sending..." : isUploading ? "Uploading..." : "Send"}
        </button>
      </div>
    </div>
  );
}
