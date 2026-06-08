"use client";
import { useState, useEffect } from "react";
import type { User } from "@/lib/types";
import { fetchMe } from "@/lib/api";

export function useMe() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchMe()
      .then(setUser)
      .catch(() => {});
  }, []);

  return { user };
}
