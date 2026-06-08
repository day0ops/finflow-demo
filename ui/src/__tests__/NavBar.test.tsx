import { render, screen, fireEvent } from "@testing-library/react";
import NavBar from "@/components/NavBar";
import type { User } from "@/lib/types";

const mockUser: User = {
  username: "alex",
  display_name: "Alex Rivera",
  role: "analyst",
};

describe("NavBar", () => {
  it("renders FINFLOW wordmark", () => {
    render(<NavBar onPoliciesClick={() => {}} />);
    expect(screen.getByText("FINFLOW")).toBeInTheDocument();
  });

  it("renders agentgateway status label", () => {
    render(<NavBar onPoliciesClick={() => {}} />);
    expect(screen.getByText("agentgateway")).toBeInTheDocument();
  });

  it("calls onPoliciesClick when Policies button pressed", () => {
    const handler = jest.fn();
    render(<NavBar onPoliciesClick={handler} />);
    fireEvent.click(screen.getByRole("button", { name: /policies/i }));
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("shows default user when no user prop provided", () => {
    render(<NavBar onPoliciesClick={() => {}} />);
    expect(screen.getByText("Morgan")).toBeInTheDocument();
    expect(screen.getByText("Trader")).toBeInTheDocument();
  });

  it("shows user identity from prop", () => {
    render(<NavBar onPoliciesClick={() => {}} user={mockUser} />);
    expect(screen.getByText("Alex Rivera")).toBeInTheDocument();
    expect(screen.getByText("Analyst")).toBeInTheDocument();
  });

  it("derives initial from display_name", () => {
    render(<NavBar onPoliciesClick={() => {}} user={mockUser} />);
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("renders sign out link", () => {
    render(<NavBar onPoliciesClick={() => {}} />);
    const link = screen.getByRole("link", { name: /sign out/i });
    expect(link).toHaveAttribute("href", "/api/logout");
  });
});
