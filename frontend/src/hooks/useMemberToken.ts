import { useState, useEffect, useCallback } from "react";

const USER_KEY = "agentroom-user";

interface UserData {
  name: string;
}

export function useMemberToken() {
  const [memberName, setMemberName] = useState<string>("");

  // Load name from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(USER_KEY);
      if (saved) {
        const data: UserData = JSON.parse(saved);
        setMemberName(data.name || "");
      }
    } catch {}
  }, []);

  // Read user_token from cookie (global identity, shared across rooms)
  const token =
    (typeof document !== "undefined" &&
      document.cookie.match(/user_token=([^;]+)/)?.[1]) ||
    "";

  const saveToken = useCallback((name: string) => {
    localStorage.setItem(USER_KEY, JSON.stringify({ name }));
    setMemberName(name);
  }, []);

  const clearToken = useCallback(() => {
    localStorage.removeItem(USER_KEY);
    setMemberName("");
  }, []);

  return { token, memberName, saveToken, clearToken };
}
