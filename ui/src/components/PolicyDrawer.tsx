import PolicyRow from "./PolicyRow";
import type { PolicyState, PolicyKey } from "@/lib/types";

interface Props {
  open: boolean;
  policies: PolicyState;
  onClose: () => void;
  onToggle: (key: PolicyKey, value: boolean) => void;
}

const POLICY_DEFS: { key: PolicyKey; label: string; desc: string }[] = [
  { key: "rbac", label: "MCP RBAC", desc: "Restrict TRADE agent to authorized roles" },
  {
    key: "elicitation",
    label: "Elicitation",
    desc: "Require confirmation before executing trades",
  },
  { key: "rate_limit", label: "Rate Limits", desc: "10 req/min per virtual key" },
  { key: "guardrails", label: "Guardrails", desc: "Block financial advice language" },
];

export default function PolicyDrawer({ open, policies, onClose, onToggle }: Props) {
  return (
    <aside className={`drawer${open ? " open" : ""}`} aria-hidden={!open}>
      <div className="drawer-header">
        <span className="drawer-title">Policies</span>
        <button className="drawer-close" onClick={onClose} aria-label="Close policies">
          ×
        </button>
      </div>
      <div className="drawer-body">
        {POLICY_DEFS.map((p) => (
          <PolicyRow
            key={p.key}
            label={p.label}
            description={p.desc}
            policyKey={p.key}
            checked={policies[p.key]}
            onToggle={onToggle}
          />
        ))}
      </div>
    </aside>
  );
}
