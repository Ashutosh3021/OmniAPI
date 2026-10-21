import { CopyButton } from "./CopyButton";
import { cn } from "@/lib/utils";

interface CodePanelProps {
  code: string;
  language?: string;
  title?: string;
  className?: string;
}

export function CodePanel({
  code,
  language = "bash",
  title,
  className,
}: CodePanelProps) {
  return (
    <figure className={cn("code-panel overflow-hidden", className)}>
      <figcaption className="flex items-center justify-between gap-3 border-b border-ink/12 px-3.5 py-2">
        <span className="font-mono text-micro uppercase tracking-[0.1em] text-muted">
          {title ?? language}
        </span>
        <CopyButton value={code} />
      </figcaption>
      <pre className="overflow-x-auto px-3.5 py-3.5 text-ink">
        <code>{code}</code>
      </pre>
    </figure>
  );
}
