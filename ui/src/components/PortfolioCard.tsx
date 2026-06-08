import type { PortfolioData } from "@/lib/types";

interface Props {
  portfolio: PortfolioData;
}

export default function PortfolioCard({ portfolio }: Props) {
  return (
    <div className="portfolio-card">
      <div className="section-label">Portfolio</div>
      <div className="portfolio-value">
        $
        {portfolio.total_value.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}
      </div>
      <div className="portfolio-total-pl">
        <span className={portfolio.total_pl >= 0 ? "pos" : "neg"}>
          {portfolio.total_pl >= 0 ? "+" : ""}$
          {Math.abs(portfolio.total_pl).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </span>
        <span
          className="portfolio-total-pl-pct"
          style={{ color: portfolio.total_pl_pct >= 0 ? "var(--green)" : "var(--red)" }}
        >
          {" "}
          {portfolio.total_pl_pct >= 0 ? "+" : ""}
          {portfolio.total_pl_pct.toFixed(2)}%
        </span>
      </div>
      {portfolio.holdings.map((h) => (
        <div key={h.ticker} className="portfolio-row">
          <div>
            <span className="portfolio-ticker">{h.ticker}</span>
            <span className="portfolio-shares"> · {h.shares} sh</span>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="portfolio-value-cell">
              $
              {h.market_value.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <div className={`portfolio-pnl ${h.pnl_pct >= 0 ? "pos" : "neg"}`}>
              {h.pnl_pct >= 0 ? "+" : ""}
              {h.pnl_pct.toFixed(2)}%
            </div>
            <div className="alloc-bar-track">
              <div
                className="alloc-bar-fill"
                style={{ width: `${((h.market_value / portfolio.total_value) * 100).toFixed(1)}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
