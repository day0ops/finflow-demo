"use client";
import TickerCard from "./TickerCard";
import PortfolioCard from "./PortfolioCard";
import AllocationDonut from "./AllocationDonut";
import NewsFeed from "./NewsFeed";
import { useTickers } from "@/hooks/useTickers";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useNews } from "@/hooks/useNews";

export default function DataPanel() {
  const { tickers } = useTickers();
  const { portfolio } = usePortfolio();
  const { news } = useNews();

  return (
    <div className="data-panel">
      <div className="data-section">
        <div className="section-label">Market</div>
        <div className="ticker-grid">
          {tickers.map((t) => (
            <TickerCard key={t.ticker} ticker={t} />
          ))}
        </div>
      </div>
      {portfolio && (
        <div className="data-section portfolio-wrap">
          <PortfolioCard portfolio={portfolio} />
          <AllocationDonut portfolio={portfolio} />
        </div>
      )}
      {news && <NewsFeed data={news} />}
    </div>
  );
}
