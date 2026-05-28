import { useState } from "react";
import { API_BASE } from "../config";
import { updateMemberRole, updateAnnouncement } from "../api/client";
import { MemoizedMarkdown } from "./MarkdownRenderer";
import type { Member, AgentStatus, MemberStats } from "../types";

interface MemberListProps {
  members: Member[];
  agentStatus: Record<string, AgentStatus>;
  showMembers: boolean;
  announcement: string;
  memberStats: Record<number, MemberStats>;
  currentRoomId: number | null;
  memberToken: string | null;
  myName: string | null;
  onRefreshMembers?: () => void;
  onDeleteRoom?: () => void;
  onUpdateAnnouncement?: () => void;
}

export default function MemberList({
  members,
  agentStatus,
  showMembers,
  announcement,
  memberStats,
  currentRoomId,
  memberToken,
  myName,
  onRefreshMembers,
  onDeleteRoom,
  onUpdateAnnouncement,
}: MemberListProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingMember, setEditingMember] = useState<Member | null>(null);
  const [editDescription, setEditDescription] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [removingMember, setRemovingMember] = useState<Member | null>(null);
  const [isRemoving, setIsRemoving] = useState(false);
  const [roleLoading, setRoleLoading] = useState<number | null>(null);
  const [editingAnnouncement, setEditingAnnouncement] = useState(false);
  const [announcementText, setAnnouncementText] = useState(announcement);
  const [savingAnnouncement, setSavingAnnouncement] = useState(false);

  const getStatus = (m: Member) => {
    const status = agentStatus[m.name];
    if (!status)
      return {
        color: "bg-[var(--status-offline)]",
        text: "Offline",
        label: "Offline",
      };
    if (status.process_online && status.listening) {
      return { color: "bg-[#00d4aa]", text: "Online", label: "Listening" };
    }
    if (status.process_online) {
      return {
        color: "bg-yellow-400",
        text: "Process",
        label: "Not listening",
      };
    }
    return {
      color: "bg-[var(--status-offline)]",
      text: "Offline",
      label: "Offline",
    };
  };

  const formatTime = (iso: string | null) => {
    if (!iso) return "Never";
    try {
      const safeIso =
        iso.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(iso) ? iso : iso + "Z";
      const d = new Date(safeIso);
      const now = new Date();
      const isToday = d.toDateString() === now.toDateString();
      const pad = (n: number) => n.toString().padStart(2, "0");
      if (isToday) return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
      return `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch {
      return "Never";
    }
  };

  const toggleExpand = (m: Member) => {
    setExpandedId((prev) => (prev === m.id ? null : m.id));
    setSaveError("");
  };

  const startEdit = (m: Member) => {
    setEditingMember(m);
    setEditDescription(m.description || "");
    setSaveError("");
  };

  const closeEdit = () => {
    setEditingMember(null);
    setSaveError("");
  };

  const saveDescription = async () => {
    if (!editingMember || !currentRoomId) return;
    setIsSaving(true);
    setSaveError("");

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (memberToken) headers["X-Member-Token"] = memberToken;

      const res = await fetch(
        `${API_BASE}/rooms/${currentRoomId}/members/${editingMember.id}/description`,
        {
          method: "PUT",
          headers,
          body: JSON.stringify({ description: editDescription }),
          credentials: "include",
        },
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed: ${res.status}`);
      }

      const updated: Member = await res.json();
      setEditingMember((prev) =>
        prev ? { ...prev, description: updated.description } : null,
      );
      closeEdit();
      onRefreshMembers?.();
    } catch (e: any) {
      setSaveError(e.message || "Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  const _findMe = () => {
    // Backend now returns is_me flag — most reliable
    let me = members.find((x) => x.is_me);
    if (!me && myName) {
      me = members.find((x) => x.name === myName);
    }
    return me;
  };

  const canEdit = (m: Member) => {
    const me = _findMe();
    return m.name === myName || me?.role === "owner" || me?.role === "admin";
  };

  const canRemove = (m: Member) => {
    if (m.name === myName) return false;
    const me = _findMe();
    return me?.role === "owner" || me?.role === "admin";
  };

  const canChangeRole = (m: Member) => {
    const me = _findMe();
    return me?.role === "owner" && m.name !== myName;
  };

  const canEditAnnouncement = (() => {
    const me = _findMe();
    return me?.role === "owner" || me?.role === "admin";
  })();

  const handleSaveAnnouncement = async () => {
    if (!currentRoomId || !memberToken) return;
    setSavingAnnouncement(true);
    try {
      const r = await updateAnnouncement(
        currentRoomId,
        announcementText,
        memberToken,
      );
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        alert(err.detail || `Failed: ${r.status}`);
        return;
      }
      setEditingAnnouncement(false);
      onUpdateAnnouncement?.();
    } catch (e: any) {
      alert(e.message || "Save failed");
    } finally {
      setSavingAnnouncement(false);
    }
  };

  const handleRoleChange = async (m: Member, newRole: string) => {
    if (!currentRoomId || !memberToken) return;
    setRoleLoading(m.id);
    try {
      const r = await updateMemberRole(
        currentRoomId,
        m.id,
        newRole,
        memberToken,
      );
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        alert(err.detail || `Failed: ${r.status}`);
        return;
      }
      onRefreshMembers?.();
    } catch (e: any) {
      alert(e.message || "Update role failed");
    } finally {
      setRoleLoading(null);
    }
  };

  const handleRemove = async () => {
    if (!removingMember || !currentRoomId || !memberToken) return;
    setIsRemoving(true);
    try {
      const res = await fetch(
        `${API_BASE}/rooms/${currentRoomId}/members/${removingMember.id}`,
        {
          method: "DELETE",
          headers: { "X-Member-Token": memberToken },
          credentials: "include",
        },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed: ${res.status}`);
      }
      setRemovingMember(null);
      onRefreshMembers?.();
    } catch (e: any) {
      alert(e.message || "Remove failed");
    } finally {
      setIsRemoving(false);
    }
  };

  return (
    <>
      <aside
        className={`fixed lg:static inset-y-0 right-0 z-50 w-64 flex-shrink-0 flex flex-col transition-transform duration-300 lg:translate-x-0 ${
          showMembers ? "translate-x-0" : "translate-x-full"
        }`}
        style={{
          borderRadius: "24px 0 0 24px",
          backgroundColor: "var(--bg-elevated)",
        }}
      >
        {/* Announcement */}
        {(announcement || editingAnnouncement || canEditAnnouncement) && (
          <div className="mx-3 mt-3 px-3 py-2.5 rounded-2xl liquid-glass">
            <div className="flex items-center justify-between mb-1">
              <div
                className="text-[10px] font-semibold uppercase tracking-wider"
                style={{ color: "#00d4aa" }}
              >
                Announcement
              </div>
              {canEditAnnouncement && !editingAnnouncement && (
                <button
                  onClick={() => {
                    setEditingAnnouncement(true);
                    setAnnouncementText(announcement);
                  }}
                  className="text-[10px] px-1.5 py-0.5 rounded-md transition-all hover:bg-white/10"
                  style={{ color: "var(--text-muted)" }}
                >
                  Edit
                </button>
              )}
            </div>
            {editingAnnouncement ? (
              <div className="space-y-2">
                <textarea
                  value={announcementText}
                  onChange={(e) => setAnnouncementText(e.target.value)}
                  rows={3}
                  className="w-full rounded-xl px-2.5 py-2 text-xs outline-none resize-none"
                  style={{
                    backgroundColor: "var(--bg-surface)",
                    border: "1px solid var(--border-color)",
                    color: "var(--text-primary)",
                  }}
                  placeholder="Enter announcement..."
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingAnnouncement(false)}
                    className="flex-1 py-1 rounded-lg text-[10px] transition-all hover:bg-white/5"
                    style={{
                      color: "var(--text-secondary)",
                      border: "1px solid var(--border-color)",
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveAnnouncement}
                    disabled={savingAnnouncement}
                    className="flex-1 py-1 rounded-lg text-[10px] font-semibold transition-all hover:opacity-90 disabled:opacity-40"
                    style={{ backgroundColor: "#00d4aa", color: "#000" }}
                  >
                    {savingAnnouncement ? "Saving..." : "Save"}
                  </button>
                </div>
              </div>
            ) : (
              <div
                className="text-xs leading-relaxed whitespace-pre-wrap"
                style={{ color: "var(--text-secondary)" }}
              >
                {announcement || "No announcement yet."}
              </div>
            )}
          </div>
        )}

        <div
          className="p-4 text-xs font-semibold uppercase tracking-wider"
          style={{ color: "var(--text-muted)" }}
        >
          Members — {members.length}
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {members.map((m) => {
            const status = getStatus(m);
            const isHuman = m.type === "human";
            const isExpanded = expandedId === m.id;
            const stats = memberStats[m.id];

            return (
              <div key={m.id}>
                <div
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-2xl transition-colors hover:bg-white/[0.05] cursor-pointer ${
                    isExpanded ? "bg-white/[0.05]" : ""
                  }`}
                  onClick={() => toggleExpand(m)}
                >
                  {!isHuman && (
                    <div
                      className={`w-2 h-2 rounded-full ${status.color} ${status.text === "Online" ? "status-pulse" : ""}`}
                      title={status.text}
                    />
                  )}
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm truncate">{m.name}</span>
                    {!isHuman && agentStatus[m.name] && (
                      <span
                        className="text-[9px]"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {status.label}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 ml-auto shrink-0">
                    {m.role && m.role !== "member" && (
                      <span
                        className="text-[9px] px-1.5 py-0.5 rounded-full"
                        style={{
                          color: "#00d4aa",
                          backgroundColor: "rgba(0,212,170,0.1)",
                          border: "1px solid rgba(0,212,170,0.2)",
                        }}
                      >
                        {m.role}
                      </span>
                    )}
                    <span
                      className="text-[10px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {m.type}
                    </span>
                  </div>
                </div>

                {/* Inline Detail Panel */}
                {isExpanded && (
                  <div
                    className="mx-1 mb-1.5 rounded-2xl p-3 space-y-3 animate-expand-in"
                    style={{ backgroundColor: "rgba(255,255,255,0.03)" }}
                  >
                    {/* Description */}
                    <div className="space-y-0.5">
                      <div
                        className="text-[10px] font-semibold uppercase tracking-wider"
                        style={{ color: "var(--text-muted)" }}
                      >
                        Description
                      </div>
                      <div
                        className="text-xs leading-relaxed"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {m.description ? (
                          <MemoizedMarkdown content={m.description} />
                        ) : (
                          "No description yet."
                        )}
                      </div>
                    </div>

                    {/* Stats */}
                    {stats && (
                      <div className="flex gap-3">
                        <div
                          className="flex-1 rounded-xl px-2 py-1.5 text-center"
                          style={{ backgroundColor: "rgba(0,212,170,0.06)" }}
                        >
                          <div
                            className="text-base font-bold"
                            style={{ color: "#00d4aa" }}
                          >
                            {stats.message_count}
                          </div>
                          <div
                            className="text-[9px]"
                            style={{ color: "var(--text-muted)" }}
                          >
                            Messages
                          </div>
                        </div>
                        <div
                          className="flex-1 rounded-xl px-2 py-1.5 text-center"
                          style={{ backgroundColor: "rgba(255,255,255,0.03)" }}
                        >
                          <div
                            className="text-base font-bold"
                            style={{ color: "var(--text-primary)" }}
                          >
                            {formatTime(stats.last_message_at)}
                          </div>
                          <div
                            className="text-[9px]"
                            style={{ color: "var(--text-muted)" }}
                          >
                            Last active
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Role */}
                    <div className="space-y-0.5">
                      <div
                        className="text-[10px] font-semibold uppercase tracking-wider"
                        style={{ color: "var(--text-muted)" }}
                      >
                        Role
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded-full"
                          style={{
                            color:
                              m.role === "owner"
                                ? "#fbbf24"
                                : m.role === "admin"
                                  ? "#60a5fa"
                                  : "var(--text-muted)",
                            backgroundColor:
                              m.role === "owner"
                                ? "rgba(251,191,36,0.1)"
                                : m.role === "admin"
                                  ? "rgba(96,165,250,0.1)"
                                  : "rgba(255,255,255,0.03)",
                            border: `1px solid ${m.role === "owner" ? "rgba(251,191,36,0.2)" : m.role === "admin" ? "rgba(96,165,250,0.2)" : "var(--border-color)"}`,
                          }}
                        >
                          {m.role || "member"}
                        </span>
                        {canChangeRole(m) && (
                          <select
                            value={m.role || "member"}
                            onChange={(e) =>
                              handleRoleChange(m, e.target.value)
                            }
                            disabled={roleLoading === m.id}
                            className="text-xs rounded-lg px-2 py-1 outline-none cursor-pointer"
                            style={{
                              backgroundColor: "var(--bg-surface)",
                              color: "var(--text-secondary)",
                              border: "1px solid var(--border-color)",
                            }}
                          >
                            <option value="member">member</option>
                            <option value="admin">admin</option>
                            <option value="owner">owner</option>
                          </select>
                        )}
                      </div>
                    </div>

                    {/* Edit button */}
                    {canEdit(m) && (
                      <button
                        onClick={() => startEdit(m)}
                        className="w-full py-1.5 rounded-xl text-xs font-medium transition-all hover:brightness-110"
                        style={{
                          backgroundColor: "rgba(0,212,170,0.1)",
                          color: "#00d4aa",
                          border: "1px solid rgba(0,212,170,0.2)",
                        }}
                      >
                        Edit Description
                      </button>
                    )}

                    {/* Remove button */}
                    {canRemove(m) && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRemovingMember(m);
                        }}
                        className="w-full py-1.5 rounded-xl text-xs font-medium transition-all hover:brightness-110"
                        style={{
                          backgroundColor: "rgba(255,59,48,0.1)",
                          color: "#ff3b30",
                          border: "1px solid rgba(255,59,48,0.2)",
                        }}
                      >
                        Remove Member
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Danger Zone — Disband Room */}
        {(() => {
          const me = _findMe();
          if (me?.role !== "owner" || !onDeleteRoom) return null;
          return (
            <div
              className="p-3 mt-auto"
              style={{ borderTop: "1px solid var(--border-color)" }}
            >
              <button
                onClick={onDeleteRoom}
                className="w-full py-2 rounded-xl text-xs font-medium transition-all hover:opacity-90"
                style={{
                  backgroundColor: "rgba(255,59,48,0.1)",
                  color: "#ff3b30",
                  border: "1px solid rgba(255,59,48,0.2)",
                }}
              >
                <span className="flex items-center justify-center gap-1.5">
                  <svg
                    width="14"
                    height="14"
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
                  Disband Room
                </span>
              </button>
            </div>
          );
        })()}
      </aside>

      {/* Edit Modal — only for editing */}
      {editingMember && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4"
          style={{ backgroundColor: "rgba(0,0,0,0.6)" }}
          onClick={closeEdit}
        >
          <div
            className="w-full max-w-sm rounded-3xl p-5 space-y-4"
            style={{ backgroundColor: "var(--bg-elevated)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-2xl flex items-center justify-center text-lg font-bold"
                  style={{
                    backgroundColor: "rgba(0,212,170,0.15)",
                    color: "#00d4aa",
                  }}
                >
                  {editingMember.name.charAt(0).toUpperCase()}
                </div>
                <div className="text-sm font-semibold">
                  {editingMember.name}
                </div>
              </div>
              <button
                onClick={closeEdit}
                className="p-1.5 rounded-xl hover:bg-white/10 transition-colors"
                style={{ color: "var(--text-muted)" }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M18 6 6 18" />
                  <path d="m6 6 12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-2">
              <div
                className="text-[10px] font-semibold uppercase tracking-wider"
                style={{ color: "var(--text-muted)" }}
              >
                Description
              </div>
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={5}
                className="w-full rounded-xl px-3 py-2 text-sm outline-none resize-none"
                style={{
                  backgroundColor: "var(--dark-surface-1)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-primary)",
                }}
                placeholder="Enter description..."
                maxLength={500}
              />
              <div
                className="text-[10px] text-right"
                style={{ color: "var(--text-muted)" }}
              >
                {editDescription.length}/500
              </div>
              {saveError && (
                <div className="text-xs text-red-400">{saveError}</div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={closeEdit}
                  className="flex-1 px-3 py-1.5 rounded-xl text-xs transition-all hover:bg-white/10"
                  style={{
                    color: "var(--text-secondary)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={saveDescription}
                  disabled={isSaving}
                  className="flex-1 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all hover:opacity-90 disabled:opacity-50"
                  style={{ backgroundColor: "#00d4aa", color: "#000" }}
                >
                  {isSaving ? "Saving..." : "Save"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Remove Confirmation Modal */}
      {removingMember && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4"
          style={{ backgroundColor: "rgba(0,0,0,0.6)" }}
          onClick={() => setRemovingMember(null)}
        >
          <div
            className="w-full max-w-sm rounded-3xl p-5 space-y-4"
            style={{ backgroundColor: "var(--bg-elevated)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-sm font-semibold">Remove Member</div>
            <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Are you sure you want to remove{" "}
              <strong>{removingMember.name}</strong> from this room? They will
              need the room secret to rejoin.
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setRemovingMember(null)}
                className="flex-1 px-3 py-1.5 rounded-xl text-xs transition-all hover:bg-white/10"
                style={{
                  color: "var(--text-secondary)",
                  border: "1px solid var(--border-color)",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleRemove}
                disabled={isRemoving}
                className="flex-1 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all hover:opacity-90 disabled:opacity-50"
                style={{ backgroundColor: "#ff3b30", color: "#fff" }}
              >
                {isRemoving ? "Removing..." : "Remove"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
