"use client";
import { useEffect, useRef } from "react";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import type { ChatMessage } from "@/lib/types";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
  onConfirm: (id: string) => void;
}

const SUGGESTED_PROMPTS = [
  "What's my portfolio worth?",
  "Give me a market briefing",
  "Buy 10 shares of NVDA",
];

export default function ChatPanel({ messages, loading, onSend, onConfirm }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">◆</div>
            <p className="chat-empty-hint">Ask about your portfolio or request a trade.</p>
            <div className="chat-suggestions">
              {SUGGESTED_PROMPTS.map((p) => (
                <button key={p} className="chat-suggestion-chip" onClick={() => onSend(p)}>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} onConfirm={onConfirm} />
        ))}
        {loading && (
          <div className="bubble bubble-ai bubble-typing">
            <div className="typing-dots">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-footer">
        <ChatInput onSend={onSend} disabled={loading} />
      </div>
    </div>
  );
}
