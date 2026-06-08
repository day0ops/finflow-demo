import type { ChatMessage } from "@/lib/types";

interface Props {
  message: ChatMessage;
  onConfirm: (id: string) => void;
}

function tagClass(tag?: string, blocked?: boolean): string {
  if (blocked) return "agent-tag agent-tag-blocked";
  if (tag === "ELICITATION") return "agent-tag agent-tag-policy";
  return "agent-tag";
}

export default function ChatBubble({ message, onConfirm }: Props) {
  if (message.role === "user") {
    return <div className="bubble bubble-user">{message.content}</div>;
  }

  return (
    <div className={`bubble bubble-ai${message.blocked ? " bubble-blocked" : ""}`}>
      {message.agent_tag && (
        <div className="bubble-meta">
          <span className={tagClass(message.agent_tag, message.blocked)}>{message.agent_tag}</span>
          {message.agent_name && <span className="bubble-agent">{message.agent_name}</span>}
          {message.latency_ms !== undefined && (
            <span className="bubble-latency">{message.latency_ms}ms</span>
          )}
        </div>
      )}
      <div>
        {message.blocked ? (
          <>
            <span className="bubble-denied">Request denied.</span>{" "}
            <span className="bubble-muted">
              {message.content.replace("Request denied.", "").trim()}
            </span>
          </>
        ) : (
          message.content
        )}
      </div>
      {message.elicitation && (
        <>
          <div style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
            {message.elicitation.trade_details}
          </div>
          <button className="btn-confirm" onClick={() => onConfirm(message.id)}>
            Confirm
          </button>
        </>
      )}
    </div>
  );
}
