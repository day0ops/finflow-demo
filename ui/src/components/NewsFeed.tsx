import type { NewsData } from "@/lib/types";

interface Props {
  data: NewsData;
}

function sentimentClass(s: string): string {
  if (s === "positive") return "news-dot pos";
  if (s === "negative") return "news-dot neg";
  return "news-dot neutral";
}

export default function NewsFeed({ data }: Props) {
  // Flatten and sort all items by date descending, keep only most recent 6
  const items = Object.entries(data.news)
    .flatMap(([ticker, articles]) => articles.map((a) => ({ ...a, ticker })))
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 6);

  if (items.length === 0) return null;

  return (
    <div className="news-feed">
      <div className="section-label">News &amp; Sentiment</div>
      {items.map((item, i) => (
        <div key={i} className="news-item">
          <span className={sentimentClass(item.sentiment)} aria-hidden="true" />
          <div className="news-content">
            <div className="news-headline">{item.headline}</div>
            <div className="news-meta">
              <span className="news-ticker">{item.ticker}</span>
              <span className="news-source">{item.source}</span>
              <span className="news-date">{item.date}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
