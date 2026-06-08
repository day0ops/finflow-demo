"use client";
import { useState, useCallback, useRef } from "react";
import type { ChatMessage, ChatApiResponse } from "@/lib/types";
import { sendChat } from "@/lib/api";

function uid() {
  return Math.random().toString(36).slice(2);
}

function agentTag(intent: string, blocked: boolean): ChatMessage["agent_tag"] {
  if (blocked) return "TRADE";
  if (intent === "briefing") return "BRIEFING";
  if (intent === "trade") return "TRADE";
  return undefined;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastTrace, setLastTrace] = useState<ChatApiResponse["trace"] | null>(null);
  const sessionId = useRef(uid());

  const appendMsg = (msg: ChatMessage) => setMessages((prev) => [...prev, msg]);

  const send = useCallback(async (text: string, confirmed = false) => {
    appendMsg({ id: uid(), role: "user", content: text });
    setLoading(true);

    try {
      const resp = await sendChat({
        message: text,
        session_id: sessionId.current,
        confirmed,
      });

      setLastTrace(resp.trace);
      const blocked = resp.trace.status_code === 403 || resp.trace.status_code === 400;
      const intent = resp.trace.intent;

      appendMsg({
        id: uid(),
        role: "assistant",
        content: resp.message,
        agent_tag: resp.elicitation ? "ELICITATION" : agentTag(intent, blocked),
        agent_name: resp.elicitation ? undefined : (resp.trace.agents[0] ?? undefined),
        latency_ms: resp.trace.latency_ms,
        policy_events: resp.trace.policy_events,
        blocked,
        elicitation: resp.elicitation ?? undefined,
      });
    } catch {
      appendMsg({
        id: uid(),
        role: "assistant",
        content: "Error: could not reach BFF. Is it running on port 8001?",
        blocked: true,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const confirm = useCallback(
    async (msgId: string) => {
      const msg = messages.find((m) => m.id === msgId);
      if (!msg?.elicitation) return;
      // Remove elicitation from the confirmed message
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, elicitation: undefined } : m))
      );
      // Find the original user message (one before this assistant message)
      const idx = messages.findIndex((m) => m.id === msgId);
      const userMsg = idx > 0 ? messages[idx - 1] : null;
      if (userMsg?.role === "user") {
        await send(userMsg.content, true);
      }
    },
    [messages, send]
  );

  return { messages, loading, lastTrace, send, confirm };
}
