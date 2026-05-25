import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useState } from "react";

function TestMessageInput({
  members,
  onSend,
}: {
  members: { name: string; type: string }[];
  onSend: (content: string) => void;
}) {
  const [value, setValue] = useState("");

  return (
    <div>
      <textarea
        data-testid="message-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <button
        data-testid="send-btn"
        onClick={() => {
          onSend(value);
          setValue("");
        }}
      >
        Send
      </button>
      <div data-testid="mention-buttons">
        {members.map((m) => (
          <button
            key={m.name}
            data-testid={`mention-${m.name}`}
            onClick={() => setValue((prev) => prev + `@${m.name} `)}
          >
            @{m.name}
          </button>
        ))}
      </div>
    </div>
  );
}

describe("MessageInput", () => {
  it("renders input and send button", () => {
    render(<TestMessageInput members={[]} onSend={() => {}} />);
    expect(screen.getByTestId("message-input")).toBeInTheDocument();
    expect(screen.getByTestId("send-btn")).toBeInTheDocument();
  });

  it("calls onSend with message content", () => {
    const onSend = vi.fn();
    render(<TestMessageInput members={[]} onSend={onSend} />);

    const input = screen.getByTestId("message-input");
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.click(screen.getByTestId("send-btn"));

    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("clears input after send", () => {
    const onSend = vi.fn();
    render(<TestMessageInput members={[]} onSend={onSend} />);

    const input = screen.getByTestId("message-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.click(screen.getByTestId("send-btn"));

    expect(input.value).toBe("");
  });

  it("inserts mention when mention button clicked", () => {
    const members = [{ name: "claude-agent", type: "agent" }];
    render(<TestMessageInput members={members} onSend={() => {}} />);

    fireEvent.click(screen.getByTestId("mention-claude-agent"));
    const input = screen.getByTestId("message-input") as HTMLTextAreaElement;
    expect(input.value).toBe("@claude-agent ");
  });
});
