import { renderHook, act } from "@testing-library/react";
import { useChat } from "@/hooks/useChat";

global.fetch = jest.fn();

afterEach(() => jest.clearAllMocks());

describe("useChat", () => {
  it("adds user message immediately on send", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: "Portfolio up 2.3%",
        trace: {
          intent: "briefing",
          agents: ["portfolio-agent"],
          latency_ms: 340,
          status_code: 200,
          policy_events: [],
        },
        elicitation: null,
      }),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.send("show portfolio");
    });

    const msgs = result.current.messages;
    expect(msgs[0].role).toBe("user");
    expect(msgs[0].content).toBe("show portfolio");
    expect(msgs[1].role).toBe("assistant");
    expect(msgs[1].content).toBe("Portfolio up 2.3%");
  });

  it("sets elicitation state when returned", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: "Confirmation required.",
        trace: {
          intent: "trade",
          agents: [],
          latency_ms: 20,
          status_code: 200,
          policy_events: [
            {
              type: "elicitation_required",
              policy: "Elicitation",
              verdict: "allow",
              message: "...",
            },
          ],
        },
        elicitation: { required: true, prompt: "Confirm trade", trade_details: "BUY 10 NVDA" },
      }),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.send("buy 10 NVDA");
    });

    const lastMsg = result.current.messages[result.current.messages.length - 1];
    expect(lastMsg.elicitation).toBeDefined();
    expect(lastMsg.elicitation?.trade_details).toBe("BUY 10 NVDA");
  });
});
