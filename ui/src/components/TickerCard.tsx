import type { TickerData } from "@/lib/types";

interface Props {
  ticker: TickerData;
}

function Sparkline({ history, isPos }: { history: TickerData["history"]; isPos: boolean }) {
  if (!history || history.length < 2) return null;

  const W = 80;
  const H = 24;
  const prices = history.map((h) => h.close);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  const pts = prices
    .map((p, i) => {
      const x = (i / (prices.length - 1)) * W;
      const y = H - ((p - min) / range) * (H - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const color = isPos ? "var(--green)" : "var(--red)";

  return (
    <svg
      className="ticker-sparkline"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function TickerCard({ ticker }: Props) {
  const isPos = ticker.change_pct >= 0;
  const sign = isPos ? "+" : "−";
  const abs = Math.abs(ticker.change_pct).toFixed(2);

  return (
    <div className="ticker-card">
      <div className="ticker-symbol">{ticker.ticker}</div>
      <div className="ticker-price">{ticker.price.toFixed(2)}</div>
      <div className={`ticker-change ${isPos ? "pos" : "neg"}`}>
        {sign}
        {abs}%
      </div>
      <Sparkline history={ticker.history} isPos={isPos} />
    </div>
  );
}
