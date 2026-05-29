"use client";

import { useState } from "react";
import { Play, Save } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Select } from "@/components/shared/Select";
import { Textarea } from "@/components/shared/Textarea";
import { Input } from "@/components/shared/Input";
import { HTTP_METHODS } from "@/lib/constants";
import { useLocalStorage } from "@/hooks/useLocalStorage";
import { useNotification } from "@/context/NotificationContext";
import { Badge } from "@/components/shared/Badge";

interface PlaygroundResponse {
  status: number;
  statusText: string;
  time: number;
  data: unknown;
  cacheHit?: boolean;
}

interface SavedRequest {
  name: string;
  method: string;
  url: string;
  headers: string;
  body: string;
}

export function APIPlayground() {
  const { notify } = useNotification();
  const [method, setMethod] = useState("GET");
  const [url, setUrl] = useState("/api/analytics");
  const [headers, setHeaders] = useState('{\n  "Content-Type": "application/json"\n}');
  const [body, setBody] = useState("{}");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<PlaygroundResponse | null>(null);
  const [saved, setSaved] = useLocalStorage<SavedRequest[]>("omniapi_quick_tests", []);

  const execute = async () => {
    setLoading(true);
    const start = Date.now();
    try {
      let parsedHeaders: Record<string, string> = {};
      try {
        parsedHeaders = JSON.parse(headers) as Record<string, string>;
      } catch {
        notify("Invalid headers JSON", "error");
        setLoading(false);
        return;
      }

      const fullUrl = url.startsWith("http") ? url : `${window.location.origin}${url.startsWith("/") ? url : `/${url}`}`;

      const res = await fetch(fullUrl, {
        method,
        headers: parsedHeaders,
        body: ["POST", "PUT", "PATCH"].includes(method) ? body : undefined,
      });

      const time = Date.now() - start;
      let data: unknown;
      try {
        data = await res.json();
      } catch {
        data = await res.text();
      }

      setResponse({
        status: res.status,
        statusText: res.statusText,
        time,
        data,
        cacheHit: res.headers.get("x-cache") === "HIT",
      });
    } catch (err) {
      setResponse({
        status: 0,
        statusText: "Error",
        time: Date.now() - start,
        data: { error: err instanceof Error ? err.message : "Request failed" },
      });
    }
    setLoading(false);
  };

  const saveTemplate = () => {
    const name = `Quick test ${saved.length + 1}`;
    setSaved([
      ...saved,
      { name, method, url, headers, body },
    ]);
    notify("Request saved as quick test", "success");
  };

  const loadTemplate = (tpl: SavedRequest) => {
    setMethod(tpl.method);
    setUrl(tpl.url);
    setHeaders(tpl.headers);
    setBody(tpl.body);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
      <div className="space-y-md">
        <h2 className="text-headline-sm font-semibold text-on-surface">Request Builder</h2>
        <div className="bg-white dark:bg-surface border border-outline-variant rounded-lg p-md space-y-md">
          <div className="flex flex-col sm:flex-row gap-sm">
            <Select
              label="Method"
              options={HTTP_METHODS.map((m) => ({ value: m, label: m }))}
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="sm:w-32"
            />
            <Input
              label="URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="/api/analytics"
              className="flex-1"
            />
          </div>
          <Textarea label="Headers (JSON)" value={headers} onChange={(e) => setHeaders(e.target.value)} rows={4} />
          {["POST", "PUT", "PATCH"].includes(method) && (
            <Textarea label="Body (JSON)" value={body} onChange={(e) => setBody(e.target.value)} rows={6} />
          )}
          <div className="flex flex-col sm:flex-row gap-md pt-md">
            <Button onClick={execute} loading={loading} fullWidth className="sm:w-auto">
              <Play className="h-4 w-4" />
              Execute
            </Button>
            <Button variant="outline" onClick={saveTemplate} fullWidth className="sm:w-auto">
              <Save className="h-4 w-4" />
              Save Template
            </Button>
          </div>
        </div>
        {saved.length > 0 && (
          <div className="space-y-sm">
            <p className="text-label-md text-on-surface-variant">Quick tests</p>
            {saved.map((tpl, i) => (
              <button
                key={i}
                type="button"
                onClick={() => loadTemplate(tpl)}
                className="block w-full text-left px-md py-sm border border-outline rounded hover:border-secondary-fixed text-body-sm"
              >
                {tpl.name} — {tpl.method} {tpl.url}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-md">
        <h2 className="text-headline-sm font-semibold text-primary-container dark:text-on-surface">Response</h2>
        <div className="bg-white dark:bg-surface border border-outline-variant rounded-lg flex flex-col min-h-[400px] lg:min-h-[500px] overflow-hidden">
          {response ? (
            <>
              <div className="border-b border-outline-variant px-md py-sm flex flex-wrap justify-between items-center gap-sm bg-surface-container-low">
                <div className="flex items-center gap-sm">
                  <Badge variant={response.status >= 200 && response.status < 300 ? "success" : "error"}>
                    {response.status} {response.statusText}
                  </Badge>
                  <span className="text-label-sm text-on-surface-variant">Time: {response.time}ms</span>
                </div>
                {response.cacheHit && (
                  <Badge variant="success">Cache Hit</Badge>
                )}
              </div>
              <pre className="flex-1 overflow-auto custom-scrollbar p-md bg-slate-800 text-gray-300 font-mono text-code text-sm">
                {JSON.stringify(response.data, null, 2)}
              </pre>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-on-surface-variant p-xl">
              Execute a request to see the response
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
