import { Component } from "react";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="flex items-center justify-center h-screen"
          style={{ backgroundColor: "var(--bg-primary)" }}
        >
          <div className="text-center p-8 rounded-2xl liquid-glass max-w-lg">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
            <p
              className="text-sm mb-4"
              style={{ color: "var(--text-secondary)" }}
            >
              Please refresh the page to continue.
            </p>
            {this.state.error && (
              <pre
                className="text-left text-xs p-3 rounded-xl mb-4 overflow-auto max-h-48"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  color: "var(--accent-coral)",
                }}
              >
                {this.state.error.toString()}
                {"\n"}
                {this.state.error.stack}
              </pre>
            )}
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-[#00d4aa] text-black text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Refresh
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
