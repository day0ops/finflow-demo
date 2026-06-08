"use client";
import { useState, useEffect } from "react";
import type { NewsData } from "@/lib/types";
import { fetchNews } from "@/lib/api";

export function useNews(refreshMs = 60_000) {
  const [news, setNews] = useState<NewsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const data = await fetchNews();
        if (alive) setNews(data);
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

  return { news, error };
}
