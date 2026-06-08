import { render, screen, fireEvent } from "@testing-library/react";
import TracePanel from "@/components/TracePanel";
import type { TraceData } from "@/lib/types";

const trace: TraceData = {
  intent: "briefing",
  agents: ["portfolio-agent", "market-data-agent"],
  latency_ms: 480,
  status_code: 200,
  policy_events: [],
};

const blockedTrace: TraceData = {
  intent: "trade",
  agents: [],
  latency_ms: 12,
  status_code: 403,
  policy_events: [
    { type: "rbac_block", policy: "MCP RBAC", verdict: "deny", message: "Requires trade role" },
  ],
};

describe("TracePanel", () => {
  it("renders collapsed summary with intent and latency", () => {
    render(<TracePanel trace={trace} />);
    expect(screen.getByText(/briefing/i)).toBeInTheDocument();
    expect(screen.getByText(/480ms/)).toBeInTheDocument();
  });

  it("expands when bar is clicked", () => {
    const { container } = render(<TracePanel trace={trace} />);
    const panel = container.querySelector(".trace-panel");
    expect(panel).not.toHaveClass("open");
    fireEvent.click(container.querySelector(".trace-bar")!);
    expect(panel).toHaveClass("open");
  });

  it("shows policy events in expanded view", () => {
    const { container } = render(<TracePanel trace={blockedTrace} />);
    fireEvent.click(container.querySelector(".trace-bar")!);
    expect(screen.getByText(/MCP RBAC/i)).toBeInTheDocument();
    expect(screen.getByText(/Requires trade role/i)).toBeInTheDocument();
  });

  it("shows agents in request flow column", () => {
    const { container } = render(<TracePanel trace={trace} />);
    fireEvent.click(container.querySelector(".trace-bar")!);
    expect(screen.getByText("portfolio-agent")).toBeInTheDocument();
    expect(screen.getByText("market-data-agent")).toBeInTheDocument();
  });
});
