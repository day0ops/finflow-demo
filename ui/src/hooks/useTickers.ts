"use client";
import { useState, useEffect } from "react";
import type { TickerData } from "@/lib/types";
import { fetchTickers } from "@/lib/api";

export function useTickers(refreshMs = 10_000) {
  const [tickers, setTickers] = useState<TickerData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const data = await fetchTickers();
        if (alive) setTickers(data);
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

  return { tickers, error };
}
