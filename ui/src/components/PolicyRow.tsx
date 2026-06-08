import type { PolicyKey } from "@/lib/types";

interface Props {
  label: string;
  description: string;
  policyKey: PolicyKey;
  checked: boolean;
  onToggle: (key: PolicyKey, value: boolean) => void;
}

export default function PolicyRow({ label, description, policyKey, checked, onToggle }: Props) {
  return (
    <div className="policy-row">
      <div className="policy-info">
        <div className="policy-name">{label}</div>
        <div className="policy-desc">{description}</div>
      </div>
      <label className="toggle" aria-label={`Toggle ${label}`}>
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onToggle(policyKey, e.target.checked)}
        />
        <span className="toggle-track">
          <span className="toggle-knob" />
        </span>
      </label>
    </div>
  );
}
