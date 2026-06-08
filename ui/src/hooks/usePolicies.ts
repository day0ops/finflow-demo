"use client";
import { useState, useEffect, useCallback } from "react";
import type { PolicyState, PolicyKey } from "@/lib/types";
import { fetchPolicies, togglePolicy } from "@/lib/api";

export function usePolicies() {
  const [policies, setPolicies] = useState<PolicyState | null>(null);

  useEffect(() => {
    fetchPolicies().then(setPolicies).catch(console.error);
  }, []);

  const toggle = useCallback(async (key: PolicyKey, value: boolean) => {
    const updated = await togglePolicy(key, value);
    setPolicies(updated);
  }, []);

  return { policies, toggle };
}
