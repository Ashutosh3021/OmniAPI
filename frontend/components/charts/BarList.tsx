interface BarListProps {
  rows: { label: string; value: number }[];
  /** The unit shown after each number. */
  unit?: string;
}

export function BarList({ rows, unit }: BarListProps) {
  const max = Math.max(...rows.map((r) => r.value), 1);

  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-ui text-muted">
        No calls recorded in this period yet.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-4">
      {rows.map((row) => (
        <li key={row.label}>
          <div className="flex items-baseline justify-between gap-4">
            <span className="truncate font-mono text-ui text-ink">
              {row.label}
            </span>
            <span className="num text-meta text-muted">
              {row.value.toLocaleString()}
              {unit ? ` ${unit}` : ""}
            </span>
          </div>
          <div className="mt-2 h-[3px] w-full bg-ink/10">
            <div
              className="h-full bg-accent transition-[width] duration-500"
              style={{ width: `${Math.max((row.value / max) * 100, 1)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
