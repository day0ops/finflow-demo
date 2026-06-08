import { renderHook, act } from "@testing-library/react";
import { usePolicies } from "@/hooks/usePolicies";

global.fetch = jest.fn();
afterEach(() => jest.clearAllMocks());

describe("usePolicies", () => {
  it("fetches policies on mount", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ rbac: false, elicitation: false, rate_limit: false, guardrails: false }),
    });
    const { result } = renderHook(() => usePolicies());
    await act(async () => {});
    expect(result.current.policies).toEqual({
      rbac: false,
      elicitation: false,
      rate_limit: false,
      guardrails: false,
    });
  });

  it("toggle calls POST and updates state", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          rbac: false,
          elicitation: false,
          rate_limit: false,
          guardrails: false,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          rbac: true,
          elicitation: false,
          rate_limit: false,
          guardrails: false,
        }),
      });

    const { result } = renderHook(() => usePolicies());
    await act(async () => {});
    await act(async () => {
      await result.current.toggle("rbac", true);
    });
    expect(result.current.policies?.rbac).toBe(true);
  });
});
