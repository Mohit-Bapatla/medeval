"use client";

import { useEffect, useState } from "react";

import { fetchApiStatus } from "@/lib/api";
import type { ApiStatus } from "@/types/status";

type LoadState = "idle" | "loading" | "ready" | "error";

export function ApiStatusPanel() {
  const [state, setState] = useState<LoadState>("idle");
  const [status, setStatus] = useState<ApiStatus | null>(null);
  const [message, setMessage] = useState<string>("Backend status has not been checked yet.");

  async function loadStatus(signal?: AbortSignal) {
    setState("loading");
    setMessage("Checking local backend...");

    try {
      const payload = await fetchApiStatus(signal);
      setStatus(payload);
      setMessage("Backend API is reachable.");
      setState("ready");
    } catch (error) {
      if (signal?.aborted) {
        return;
      }
      setStatus(null);
      setMessage(error instanceof Error ? error.message : "Backend API is not reachable.");
      setState("error");
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void loadStatus(controller.signal);
    return () => controller.abort();
  }, []);

  const badgeClass =
    state === "ready"
      ? "border-clinical/30 bg-clinical/10 text-clinical"
      : state === "error"
        ? "border-signal/30 bg-signal/10 text-signal"
        : "border-line bg-white text-graphite";

  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase text-graphite">Local API</p>
          <h2 className="mt-1 text-xl font-semibold text-ink">Backend status</h2>
        </div>
        <span className={`w-fit rounded-full border px-3 py-1 text-sm font-medium ${badgeClass}`}>
          {state === "ready" ? "Connected" : state === "error" ? "Offline" : "Checking"}
        </span>
      </div>

      <p className="mt-4 text-sm leading-6 text-graphite">{message}</p>

      {status ? (
        <div className="mt-4 grid gap-3 text-sm text-graphite">
          <div>
            <span className="font-semibold text-ink">{status.name}</span>
            <span> - {status.version}</span>
          </div>
          <div>{status.purpose}</div>
          <div className="flex flex-wrap gap-2">
            {status.modules.map((module) => (
              <span key={module} className="rounded-md border border-line px-2 py-1">
                {module}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <button
        className="mt-5 rounded-md border border-line bg-surface px-3 py-2 text-sm font-medium text-ink hover:bg-white"
        type="button"
        onClick={() => void loadStatus()}
      >
        Refresh status
      </button>
    </section>
  );
}
