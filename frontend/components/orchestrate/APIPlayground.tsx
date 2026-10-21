"use client";

import { useEffect, useMemo, useState } from "react";
import { Play, RotateCcw } from "lucide-react";
import { FanDiagram } from "@/components/fan/FanDiagram";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { CodePanel } from "@/components/shared/CodePanel";
import { EmptyState } from "@/components/shared/EmptyState";
import { Spinner } from "@/components/shared/Spinner";
import { Textarea } from "@/components/shared/Textarea";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import type { ExternalService } from "@/types";

interface OrchestrateResult {
  service: string;
  success: boolean;
  data?: Record<string, unknown> | null;
  error?: string | null;
  response_time_ms: number;
  cache_hit: boolean;
}

interface OrchestrateResponse {
  request_id: string;
  results: OrchestrateResult[];
  total_time_ms: number;
  timestamp: string;
}

const DEFAULT_PARAMS = `{
  "weather": { "city": "Lisbon" }
}`;

export function APIPlayground() {
  const [services, setServices] = useState<ExternalService[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [response, setResponse] = useState<OrchestrateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { notify } = useNotification();

  useEffect(() => {
    let cancelled = false;
    api
      .get<ExternalService[]>("/external-services")
      .then((list) => {
        if (cancelled) return;
        setServices(list);
        setSelected((prev) =>
          prev.length
            ? prev
            : list.slice(0, Math.min(3, list.length)).map((s) => s.service_name)
        );
      })
      .catch(() => {
        if (!cancelled) setError("Could not load your services.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const toggle = (name: string) =>
    setSelected((prev) =>
      prev.includes(name)
        ? prev.filter((n) => n !== name)
        : [...prev, name]
    );

  const execute = async () => {
    if (selected.length === 0) {
      notify("Pick at least one service first", "warning");
      return;
    }

    let parsed: Record<string, Record<string, unknown>> = {};
    try {
      parsed = params.trim() ? JSON.parse(params) : {};
    } catch {
      notify("The params block is not valid JSON", "error");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.post<OrchestrateResponse>("/orchestrate", {
        services: selected,
        params: parsed,
      });
      setResponse(res);
    } catch (err) {
      setResponse(null);
      setError(
        err instanceof Error
          ? err.message
          : "The gateway did not answer. Check your services and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const fanServices = useMemo(
    () =>
      (response?.results ?? []).map((r) => ({
        name: r.service,
        latencyMs: r.response_time_ms,
        cached: r.cache_hit,
      })),
    [response]
  );

  const requestBody = useMemo(
    () =>
      JSON.stringify(
        {
          services: selected,
          params: (() => {
            try {
              return params.trim() ? JSON.parse(params) : {};
            } catch {
              return {};
            }
          })(),
        },
        null,
        2
      ),
    [selected, params]
  );

  return (
    <div className="grid grid-cols-1 gap-gutter lg:grid-cols-12">
      {/* The request. */}
      <section className="lg:col-span-5" aria-label="Request">
        <div className="panel p-5 md:p-7">
          <div className="mb-5 flex items-baseline justify-between gap-3">
            <h2 className="t-subhead text-ink">Request</h2>
            <span className="label-wire">POST /orchestrate</span>
          </div>

          {services.length === 0 ? (
            <EmptyState
              title="No services connected."
              description="Connect a provider first. The playground can only call the services you have registered."
            />
          ) : (
            <>
              <fieldset className="mb-5">
                <legend className="label-wire mb-2.5">Services</legend>
                <ul className="flex flex-col gap-1.5">
                  {services.map((svc) => {
                    const active = selected.includes(svc.service_name);
                    return (
                      <li key={svc.service_id}>
                        <button
                          type="button"
                          onClick={() => toggle(svc.service_name)}
                          aria-pressed={active}
                          className={
                            active
                              ? "flex w-full items-center gap-2.5 rounded border border-accent/45 bg-accent/8 px-3 py-2 text-left text-ui text-ink transition-colors"
                              : "flex w-full items-center gap-2.5 rounded border border-ink/15 px-3 py-2 text-left text-ui text-muted transition-colors hover:border-ink/30 hover:text-ink"
                          }
                        >
                          <span
                            className={active ? "lamp bg-accent" : "lamp lamp-idle"}
                            aria-hidden
                          />
                          <span className="font-mono text-[0.8125rem]">
                            {svc.service_name}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </fieldset>

              <Textarea
                label="Params"
                value={params}
                onChange={(e) => setParams(e.target.value)}
                mono
                rows={8}
                hint="One object per service, keyed by service name."
              />

              <div className="mt-5 flex flex-wrap items-center gap-2">
                <Button onClick={execute} loading={loading}>
                  <Play className="h-4 w-4" aria-hidden />
                  Execute
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setResponse(null);
                    setError(null);
                  }}
                  disabled={!response && !error}
                >
                  <RotateCcw className="h-4 w-4" aria-hidden />
                  Clear
                </Button>
              </div>
            </>
          )}
        </div>

        <div className="mt-4">
          <CodePanel title="body" language="json" code={requestBody} />
        </div>
      </section>

      {/* The answer. */}
      <section className="lg:col-span-7" aria-label="Response">
        <div className="panel p-5 md:p-7">
          <div className="mb-5 flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="t-subhead text-ink">Response</h2>
            {response && (
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="accent">{response.total_time_ms} ms total</Badge>
                <span className="font-mono text-micro text-muted">
                  {response.request_id}
                </span>
              </div>
            )}
          </div>

          {loading ? (
            <Spinner label="Calling the gateway" />
          ) : error ? (
            <div className="rounded border border-bad/35 bg-bad/8 p-4">
              <p className="label-wire mb-1.5 text-bad">failed</p>
              <p className="text-ui text-ink">{error}</p>
            </div>
          ) : response ? (
            <>
              {fanServices.length > 0 && (
                <div className="mb-6">
                  <FanDiagram services={fanServices} mode="live" />
                </div>
              )}

              <ul className="mb-6 flex flex-col gap-2">
                {response.results.map((r) => (
                  <li
                    key={r.service}
                    className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-ink/12 pb-2 last:border-0"
                  >
                    <span className="font-mono text-[0.8125rem] text-ink">
                      {r.service}
                    </span>
                    <Badge tone={r.success ? "ok" : "bad"}>
                      {r.success ? "ok" : "failed"}
                    </Badge>
                    {r.cache_hit && <Badge tone="neutral">cached</Badge>}
                    <span className="num text-meta text-muted">
                      {r.response_time_ms} ms
                    </span>
                    {r.error && (
                      <span className="text-meta text-bad">{r.error}</span>
                    )}
                  </li>
                ))}
              </ul>

              <CodePanel
                title="response body"
                language="json"
                code={JSON.stringify(response, null, 2)}
              />
            </>
          ) : (
            <EmptyState
              title="Nothing has been called yet."
              description="Pick your services and run the request. The fan shows how long each branch took and whether the answer came from the cache."
            />
          )}
        </div>
      </section>
    </div>
  );
}
