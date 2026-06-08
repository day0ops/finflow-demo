import type { User } from "@/lib/types";

interface NavBarProps {
  onPoliciesClick: () => void;
  user?: User | null;
}

export default function NavBar({ onPoliciesClick, user }: NavBarProps) {
  const displayName = user?.display_name ?? "Morgan";
  const role = user?.role ?? "trader";
  const initial = displayName.charAt(0).toUpperCase();
  const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);

  return (
    <nav className="nav">
      <div className="nav-left">
        <button className="nav-policies-btn" onClick={onPoliciesClick}>
          Policies
        </button>
        <span className="nav-wordmark">FINFLOW</span>
      </div>
      <div className="nav-right">
        <div className="nav-user-badge" aria-label={`Signed in as ${displayName}`}>
          <span className="nav-user-initials" aria-hidden="true">
            {initial}
          </span>
          <div className="nav-user-info">
            <span className="nav-user-name">{displayName}</span>
            <span className="nav-user-role">{roleLabel}</span>
          </div>
        </div>
        <a href="/api/logout" className="nav-logout-btn" aria-label="Sign out">
          Sign out
        </a>
        <span className="nav-status-dot" aria-label="agentgateway connected" />
        <span className="nav-status-label">agentgateway</span>
      </div>
    </nav>
  );
}
