import { useEffect, useState } from "react";
import { API_BASE } from "../config";

interface AgentHome {
  name: string;
  description: string;
  owner: string;
  avatar: string;
}

interface AgentsPageProps {
  onBack?: () => void;
}

export default function AgentsPage({ onBack }: AgentsPageProps) {
  const [agents, setAgents] = useState<AgentHome[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/agents`)
      .then((r) => r.json())
      .then((data) => {
        setAgents(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div
        className="flex-1 flex items-center justify-center"
        style={{ color: "var(--text-muted)" }}
      >
        Loading agents...
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 rounded-xl transition-all btn-press"
              style={{
                backgroundColor: "var(--bg-surface)",
                color: "var(--text-secondary)",
              }}
              title="Back"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
            </button>
          )}
          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            My Agents
          </h1>
        </div>

        {agents.length === 0 ? (
          <div
            className="text-center py-20 rounded-2xl"
            style={{
              backgroundColor: "var(--bg-secondary)",
              color: "var(--text-muted)",
            }}
          >
            <p className="text-lg mb-2">No agents yet</p>
            <p className="text-sm">
              Create an agent home in ~/.agentroom/agents/ to get started
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className="rounded-2xl p-5 transition-all hover:brightness-110 cursor-pointer"
                style={{ backgroundColor: "var(--bg-secondary)" }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
                    style={{
                      backgroundColor: "var(--accent-blue)",
                      color: "#fff",
                    }}
                  >
                    {agent.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3
                      className="font-semibold text-sm truncate"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {agent.name}
                    </h3>
                    {agent.owner && (
                      <p
                        className="text-xs truncate"
                        style={{ color: "var(--text-muted)" }}
                      >
                        Owner: {agent.owner}
                      </p>
                    )}
                  </div>
                </div>
                {agent.description && (
                  <p
                    className="text-sm line-clamp-2"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {agent.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
