"use client";
import { useState, useEffect } from "react";
import type { PortfolioData } from "@/lib/types";
import { fetchPortfolio } from "@/lib/api";

export function usePortfolio(refreshMs = 30_000) {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const data = await fetchPortfolio();
        if (alive) setPortfolio(data);
      } catch (e) {
        if (alive) setError(String(e));
      }
    }

    load();
    const id = setInterval(load, refreshMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [refreshMs]);

  return { portfolio, error };
}
