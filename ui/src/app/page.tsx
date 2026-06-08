"use client";
import { useState } from "react";
import NavBar from "@/components/NavBar";
import ChatPanel from "@/components/ChatPanel";
import DataPanel from "@/components/DataPanel";
import PolicyDrawer from "@/components/PolicyDrawer";
import TracePanel from "@/components/TracePanel";
import { useChat } from "@/hooks/useChat";
import { usePolicies } from "@/hooks/usePolicies";
import { useMe } from "@/hooks/useMe";

export default function Page() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { messages, loading, lastTrace, send, confirm } = useChat();
  const { policies, toggle } = usePolicies();
  const { user } = useMe();

  return (
    <div className="app-shell">
      <NavBar onPoliciesClick={() => setDrawerOpen((v) => !v)} user={user} />

      <div className="layout">
        <PolicyDrawer
          open={drawerOpen}
          policies={
            policies ?? { rbac: false, elicitation: false, rate_limit: false, guardrails: false }
          }
          onClose={() => setDrawerOpen(false)}
          onToggle={toggle}
        />

        <div className={`content${drawerOpen ? " pushed" : ""}`}>
          <ChatPanel messages={messages} loading={loading} onSend={send} onConfirm={confirm} />
          <DataPanel />
        </div>

        <TracePanel trace={lastTrace} />
      </div>
    </div>
  );
}
