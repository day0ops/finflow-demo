"use client";
import { useState } from "react";
import type { TraceData } from "@/lib/types";

interface Props {
  trace: TraceData | null;
}

function dotClass(verdict: string): string {
  if (verdict === "deny") return "trace-event-dot deny";
  if (verdict === "allow") return "trace-event-dot allow";
  return "trace-event-dot info";
}

export default function TracePanel({ trace }: Props) {
  const [open, setOpen] = useState(false);

  const summary = trace
    ? `${trace.intent} · ${trace.agents.length} agent${trace.agents.length !== 1 ? "s" : ""} · ${trace.latency_ms}ms`
    : "No trace yet";

  return (
    <div className={`trace-panel${open ? " open" : ""}`}>
      <div
        className="trace-bar"
        role="button"
        tabIndex={0}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => e.key === "Enter" && setOpen((v) => !v)}
      >
        <span className="trace-summary">{summary}</span>
        <span className="trace-chevron">▲</span>
      </div>

      {open && trace && (
        <div className="trace-body">
          <div>
            <div className="trace-col-label">Request Flow</div>
            {trace.agents.length === 0 && (
              <div className="trace-event">
                <span className="trace-event-dot deny" />
                <span className="trace-event-text">No agents called</span>
              </div>
            )}
            {trace.agents.map((a, i) => (
              <div key={i} className="trace-event">
                <span className="trace-event-dot allow" />
                <span className="trace-event-text">{a}</span>
              </div>
            ))}
            <div className="trace-event" style={{ marginTop: 4 }}>
              <span className="trace-event-dot info" />
              <span className="trace-event-text">
                HTTP {trace.status_code} · {trace.latency_ms}ms
              </span>
            </div>
          </div>

          <div>
            <div className="trace-col-label">Auth &amp; Routing</div>
            {trace.policy_events.length === 0 ? (
              <div className="trace-event">
                <span className="trace-event-dot allow" />
                <span className="trace-event-text">No policy events</span>
              </div>
            ) : (
              trace.policy_events.map((ev, i) => (
                <div key={i} className="trace-event">
                  <span className={dotClass(ev.verdict)} />
                  <div className="trace-event-text">
                    <div style={{ fontWeight: 600 }}>{ev.policy}</div>
                    <div style={{ color: "var(--muted)" }}>{ev.message}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
