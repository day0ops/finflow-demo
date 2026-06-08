import type { PortfolioData } from "@/lib/types";

interface Props {
  portfolio: PortfolioData;
}

// Signal Blue at varying opacities for each slice
const SLICE_COLORS = [
  "rgba(29,138,255,1.0)",
  "rgba(29,138,255,0.65)",
  "rgba(29,138,255,0.42)",
  "rgba(29,138,255,0.28)",
  "rgba(29,138,255,0.18)",
];

const SIZE = 96;
const STROKE = 14;
const R = (SIZE - STROKE) / 2;
const CIRC = 2 * Math.PI * R;

export default function AllocationDonut({ portfolio }: Props) {
  const { holdings, total_value } = portfolio;
  if (!holdings.length || total_value === 0) return null;

  // Build slices with cumulative offset
  let offset = 0;
  const slices = holdings.map((h, i) => {
    const pct = h.market_value / total_value;
    const dash = pct * CIRC;
    const gap = CIRC - dash;
    const slice = { ...h, dash, gap, offset, color: SLICE_COLORS[i % SLICE_COLORS.length] };
    offset += dash;
    return slice;
  });

  const cx = SIZE / 2;
  const cy = SIZE / 2;

  return (
    <div className="alloc-donut-wrap">
      <div className="section-label">Allocation</div>
      <div className="alloc-donut-row">
        <svg
          className="alloc-donut-svg"
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          aria-label="Portfolio allocation donut chart"
        >
          {/* Background ring */}
          <circle
            cx={cx}
            cy={cy}
            r={R}
            fill="none"
            stroke="rgba(29,138,255,0.08)"
            strokeWidth={STROKE}
          />
          {slices.map((s) => (
            <circle
              key={s.ticker}
              cx={cx}
              cy={cy}
              r={R}
              fill="none"
              stroke={s.color}
              strokeWidth={STROKE}
              strokeDasharray={`${s.dash} ${s.gap}`}
              strokeDashoffset={-s.offset}
              strokeLinecap="butt"
              style={{ transform: "rotate(-90deg)", transformOrigin: "center" }}
            />
          ))}
        </svg>
        <div className="alloc-legend">
          {slices.map((s, i) => (
            <div key={s.ticker} className="alloc-legend-row">
              <span
                className="alloc-legend-dot"
                style={{ background: SLICE_COLORS[i % SLICE_COLORS.length] }}
              />
              <span className="alloc-legend-ticker">{s.ticker}</span>
              <span className="alloc-legend-pct">
                {((s.market_value / total_value) * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
