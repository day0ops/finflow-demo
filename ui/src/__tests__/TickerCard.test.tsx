import { render, screen } from "@testing-library/react";
import TickerCard from "@/components/TickerCard";

const nvda = {
  ticker: "NVDA",
  name: "NVIDIA Corp",
  price: 134.87,
  change_pct: 2.41,
  volume: 48203100,
  history: [],
};
const aapl = {
  ticker: "AAPL",
  name: "Apple Inc",
  price: 211.5,
  change_pct: -0.83,
  volume: 52108400,
  history: [],
};

describe("TickerCard", () => {
  it("renders ticker symbol", () => {
    render(<TickerCard ticker={nvda} />);
    expect(screen.getByText("NVDA")).toBeInTheDocument();
  });

  it("renders positive change in green class", () => {
    render(<TickerCard ticker={nvda} />);
    const change = screen.getByText(/\+2\.41%/);
    expect(change).toHaveClass("pos");
  });

  it("renders negative change in red class", () => {
    render(<TickerCard ticker={aapl} />);
    const change = screen.getByText(/−0\.83%/);
    expect(change).toHaveClass("neg");
  });
});
