import { render, screen, fireEvent } from "@testing-library/react";
import PolicyDrawer from "@/components/PolicyDrawer";
import type { PolicyState } from "@/lib/types";

const policies: PolicyState = {
  rbac: false,
  elicitation: true,
  rate_limit: false,
  guardrails: false,
};

describe("PolicyDrawer", () => {
  it("renders all four policy names", () => {
    render(<PolicyDrawer open={true} policies={policies} onClose={() => {}} onToggle={() => {}} />);
    expect(screen.getByText("MCP RBAC")).toBeInTheDocument();
    expect(screen.getByText("Elicitation")).toBeInTheDocument();
    expect(screen.getByText("Rate Limits")).toBeInTheDocument();
    expect(screen.getByText("Guardrails")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    const onClose = jest.fn();
    render(<PolicyDrawer open={true} policies={policies} onClose={onClose} onToggle={() => {}} />);
    fireEvent.click(screen.getByLabelText(/close policies/i));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onToggle with key and new value when toggle clicked", () => {
    const onToggle = jest.fn();
    render(<PolicyDrawer open={true} policies={policies} onClose={() => {}} onToggle={onToggle} />);
    // RBAC is off (false) — click its toggle → expect (rbac, true)
    const toggles = screen.getAllByRole("checkbox");
    fireEvent.click(toggles[0]); // first is RBAC
    expect(onToggle).toHaveBeenCalledWith("rbac", true);
  });
});
