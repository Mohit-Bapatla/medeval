"use client";

import { useEffect, useState } from "react";

import { fetchApiStatus } from "@/lib/api";
import type { ApiStatus } from "@/types/status";

type LoadState = "idle" | "loading" | "ready" | "error";

export function ApiStatusPanel() {
  const [state, setState] = useState<LoadState>("idle");
  const [status, setStatus] = useState<ApiStatus | null>(null);
  const [message, setMessage] = useState<string>(
    "Backend status has not been checked yet.",
  );

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
      setMessage(
        error instanceof Error
          ? error.message
          : "Backend API is not reachable.",
      );
      setState("error");
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void loadStatus(controller.signal);
    return () => controller.abort();
  }, []);

  const statusConfig =
    state === "ready"
      ? {
          dot: "bg-success",
          badge: "border-success/30 bg-success/10 text-success",
          label: "Connected",
        }
      : state === "error"
        ? {
            dot: "bg-danger",
            badge: "border-danger/30 bg-danger/10 text-danger",
            label: "Offline",
          }
        : {
            dot: "bg-signal animate-pulse",
            badge: "border-signal/30 bg-signal/10 text-signal",
            label: "Checking",
          };

  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-graphite">
            Local API
          </p>
          <h2 className="mt-1 text-base font-semibold text-ink">
            Backend status
          </h2>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${statusConfig.badge}`}
        >
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${statusConfig.dot}`}
          />
          {statusConfig.label}
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-graphite">{message}</p>

      {status ? (
        <div className="mt-4 space-y-2 text-sm text-graphite">
          <div>
            <span className="font-semibold text-ink">{status.name}</span>
            <span className="ml-1 text-xs text-graphite">— {status.version}</span>
          </div>
          <div className="text-xs">{status.purpose}</div>
          <div className="flex flex-wrap gap-1.5">
            {status.modules.map((module) => (
              <span
                key={module}
                className="rounded-md border border-line bg-surface px-2 py-0.5 text-xs text-graphite"
              >
                {module}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <button
        className="mt-4 rounded-md border border-line bg-surface px-3 py-1.5 text-xs font-medium text-ink transition-colors hover:bg-white hover:border-graphite"
        type="button"
        onClick={() => void loadStatus()}
      >
        Refresh status
      </button>
    </section>
  );
}
