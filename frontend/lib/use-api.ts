"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";

export type ApiState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
};

export function useApi<T>(path: string | null): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    if (!path) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(null);

    apiFetch<T>(path, { signal: controller.signal })
      .then((payload) => {
        setData(payload);
      })
      .catch((caught) => {
        if (controller.signal.aborted) {
          return;
        }
        setData(null);
        setError(caught instanceof Error ? caught.message : "Unable to load API data.");
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [path, reloadKey]);

  return { data, error, loading, reload };
}
