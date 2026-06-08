import { render, screen, fireEvent } from "@testing-library/react";
import ChatBubble from "@/components/ChatBubble";
import type { ChatMessage } from "@/lib/types";

const userMsg: ChatMessage = {
  id: "1",
  role: "user",
  content: "Show my portfolio",
};
const aiMsg: ChatMessage = {
  id: "2",
  role: "assistant",
  content: "Portfolio up 2.3%",
  agent_tag: "BRIEFING",
  agent_name: "portfolio-agent",
  latency_ms: 340,
};
const blockedMsg: ChatMessage = {
  id: "3",
  role: "assistant",
  content: "Request denied.",
  agent_tag: "TRADE",
  blocked: true,
};

describe("ChatBubble", () => {
  it("renders user bubble with bubble-user class", () => {
    const { container } = render(<ChatBubble message={userMsg} onConfirm={() => {}} />);
    expect(container.querySelector(".bubble-user")).toBeInTheDocument();
    expect(screen.getByText("Show my portfolio")).toBeInTheDocument();
  });

  it("renders AI bubble with agent tag and latency", () => {
    render(<ChatBubble message={aiMsg} onConfirm={() => {}} />);
    expect(screen.getByText("BRIEFING")).toBeInTheDocument();
    expect(screen.getByText("portfolio-agent")).toBeInTheDocument();
    expect(screen.getByText("340ms")).toBeInTheDocument();
  });

  it("renders blocked bubble with blocked class", () => {
    const { container } = render(<ChatBubble message={blockedMsg} onConfirm={() => {}} />);
    expect(container.querySelector(".bubble-blocked")).toBeInTheDocument();
  });
});
