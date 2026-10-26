"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { gsap } from "gsap";
import { prefersReducedMotion } from "@/lib/engine";
import { formatLatency, layoutFor, type FanService } from "@/lib/motion/fan";

type FanMode = "live" | "loop" | "static";

interface FanDiagramProps {
  services: FanService[];
  /** live: plays once. loop: repeats. static: draws the finished diagram. */
  mode?: FanMode;
  caption?: string;
  className?: string;
  onGathered?: () => void;
}

function useVertical() {
  const [vertical, setVertical] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 767px)");
    const update = () => setVertical(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return vertical;
}

export function FanDiagram({
  services,
  mode = "live",
  caption,
  className,
  onGathered,
}: FanDiagramProps) {
  const vertical = useVertical();

  // A stable key so the animation only restarts when the content changes,
  // not on every parent render.
  const signature = services
    .map(
      (s) =>
        `${s.name}:${s.latencyMs ?? ""}:${s.meta ?? ""}:${s.cached ? 1 : 0}`
    )
    .join("|");

  const geometry = useMemo(
    () => layoutFor(services, vertical),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [signature, vertical]
  );

  const rootRef = useRef<HTMLDivElement>(null);
  const signalRefs = useRef<(SVGPathElement | null)[]>([]);
  const flowRefs = useRef<(SVGPathElement | null)[]>([]);
  const gatherRefs = useRef<(SVGPathElement | null)[]>([]);
  const nodeRefs = useRef<(SVGGElement | null)[]>([]);
  const envelopeRef = useRef<SVGGElement>(null);
  const originRef = useRef<SVGCircleElement>(null);
  const gatheredRef = useRef(onGathered);
  gatheredRef.current = onGathered;

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const reduced = prefersReducedMotion();
    const ctx = gsap.context(() => {
      const signals = signalRefs.current.filter(Boolean) as SVGPathElement[];
      const flows = flowRefs.current.filter(Boolean) as SVGPathElement[];
      const gathers = gatherRefs.current.filter(Boolean) as SVGPathElement[];
      const nodes = nodeRefs.current.filter(Boolean) as SVGGElement[];

      const signalLengths = signals.map((el) => el.getTotalLength());
      const gatherLengths = gathers.map((el) => el.getTotalLength());

      signals.forEach((el) =>
        gsap.set(el, { strokeDasharray: "22 4000", strokeDashoffset: 0 })
      );
      gathers.forEach((el) =>
        gsap.set(el, { strokeDasharray: "18 4000", strokeDashoffset: 0 })
      );

      // The idle state: a soft signal always travelling along every branch.
      // It never stops, so the diagram is alive even when nothing is called.
      if (!reduced) {
        flows.forEach((el, i) => {
          const len = el.getTotalLength() || 1;
          gsap.set(el, {
            strokeDasharray: `${len * 0.3} ${len}`,
            strokeDashoffset: 0,
          });
          gsap.fromTo(
            el,
            { strokeDashoffset: 0 },
            {
              strokeDashoffset: -len,
              duration: 3.2 + i * 0.45,
              ease: "none",
              repeat: -1,
            }
          );
        });
      }

      const draw = (master: gsap.core.Timeline) => {
        const travel = (ms?: number) =>
          Math.min(Math.max((ms ?? 400) / 1000 * 0.55, 0.5), 1.5);
        const longest = Math.max(
          ...services.map((s) => travel(s.latencyMs)),
          0.5
        );

        signals.forEach((el, i) => {
          const len = signalLengths[i] || 1;
          master.fromTo(
            el,
            { strokeDashoffset: 0, opacity: 1 },
            {
              strokeDashoffset: -len,
              duration: travel(services[i]?.latencyMs),
              ease: "power2.out",
            },
            i * 0.09
          );
        });

        nodes.forEach((node, i) => {
          master.fromTo(
            node,
            { opacity: 0, y: 6 },
            {
              opacity: 1,
              y: 0,
              duration: 0.4,
              ease: "power3.out",
            },
            i * 0.09 + travel(services[i]?.latencyMs) * 0.72
          );
        });

        // Hold: every branch has answered before anything gathers back.
        master.to({}, { duration: 0.7 }, longest + 0.25);

        gathers.forEach((el, i) => {
          const len = gatherLengths[i] || 1;
          master.fromTo(
            el,
            { strokeDashoffset: 0, opacity: 1 },
            {
              strokeDashoffset: -len,
              duration: 0.5,
              ease: "power2.out",
            },
            longest + 0.35 + i * 0.07
          );
        });

        if (envelopeRef.current) {
          master.fromTo(
            envelopeRef.current,
            { opacity: 0, scale: 0.94, transformOrigin: "50% 50%" },
            { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.4)" },
            longest + 0.62
          );
        }

        master.to({}, { duration: 0.2 });
      };

      if (reduced || mode === "static") {
        signals.forEach((el) =>
          gsap.set(el, { opacity: 0.6, strokeDasharray: "none", strokeDashoffset: 0 })
        );
        gathers.forEach((el) =>
          gsap.set(el, { opacity: 0.6, strokeDasharray: "none", strokeDashoffset: 0 })
        );
        nodes.forEach((n) => gsap.set(n, { opacity: 1, y: 0 }));
        if (envelopeRef.current)
          gsap.set(envelopeRef.current, { opacity: 1, scale: 1 });
        if (originRef.current) gsap.set(originRef.current, { opacity: 1, scale: 1 });
        return;
      }

      gsap.set(nodes, { opacity: 0, y: 6 });
      if (envelopeRef.current)
        gsap.set(envelopeRef.current, { opacity: 0, scale: 0.94 });
      if (originRef.current)
        gsap.set(originRef.current, { opacity: 0, scale: 0.6 });

      // One timeline, repeated. Every tween is a fromTo, so each cycle
      // resets itself: no manual state juggling between iterations.
      const tl = gsap.timeline({ repeat: mode === "loop" ? -1 : 0 });
      tl.fromTo(
        originRef.current,
        { opacity: 0, scale: 0.6 },
        { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" },
        0
      );
      draw(tl);
      tl.add(() => gatheredRef.current?.(), ">-0.1");
      if (mode === "loop") tl.to({}, { duration: 1.1 }, ">");
    }, root);

    return () => ctx.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, mode, geometry]);

  const summary = services
    .map((s) => `${s.name}${s.latencyMs ? ` ${formatLatency(s.latencyMs)}` : ""}`)
    .join(", ");

  return (
    <figure className={className}>
      <div ref={rootRef} className="relative w-full">
        <svg
          viewBox={`0 0 ${geometry.width} ${geometry.height}`}
          className="w-full h-auto"
          role="img"
          aria-label={`Request fan: ${summary}`}
        >
          {/* The spine: where every call leaves from. */}
          <line
            x1={geometry.spine.x1}
            y1={geometry.spine.y1}
            x2={geometry.spine.x2}
            y2={geometry.spine.y2}
            className="fan-spine fan-spine-base"
          />
          <line
            data-pulse
            x1={geometry.spine.x1}
            y1={geometry.spine.y1}
            x2={geometry.spine.x2}
            y2={geometry.spine.y2}
            className="fan-pulse"
          />

          {/* Wires, always present. */}
          {geometry.branches.map((b) => (
            <path key={`wire-${b.id}`} d={b.d} className="fan-branch fan-branch--idle" />
          ))}
          {geometry.gathers.map((g) => (
            <path key={`wire-${g.id}`} d={g.d} className="fan-branch fan-branch--idle" />
          ))}

          {/* The signal: one dash per branch, travelling out and back. */}
          {geometry.branches.map((b, i) => (
            <path
              key={`flow-${b.id}`}
              d={b.d}
              className="fan-flow"
              ref={(el) => {
                flowRefs.current[i] = el;
              }}
            />
          ))}
          {geometry.branches.map((b, i) => (
            <path
              key={b.id}
              d={b.d}
              className="fan-branch"
              ref={(el) => {
                signalRefs.current[i] = el;
              }}
            />
          ))}
          {geometry.gathers.map((g, i) => (
            <path
              key={g.id}
              d={g.d}
              className="fan-branch"
              ref={(el) => {
                gatherRefs.current[i] = el;
              }}
            />
          ))}

          <circle
            ref={originRef}
            cx={geometry.origin.x}
            cy={geometry.origin.y}
            r={5}
            className="fan-packet"
          />

          {/* Service nodes. */}
          {services.map((s, i) => {
            const node = geometry.nodes[i];
            if (!node) return null;
            return (
              <g
                key={s.name}
                ref={(el) => {
                  nodeRefs.current[i] = el;
                }}
              >
                {node.boxed && (
                  <rect
                    x={node.x}
                    y={node.y}
                    width={node.w}
                    height={node.h}
                    rx={4}
                    className="fan-envelope"
                  />
                )}
                {!node.boxed && (
                  <circle
                    cx={geometry.branches[i]?.end.x ?? 0}
                    cy={geometry.branches[i]?.end.y ?? 0}
                    r={3}
                    className="fan-packet"
                  />
                )}
                <text
                  x={node.labelX}
                  y={node.labelY}
                  className="fan-label fill-ink"
                >
                  {s.name}
                </text>
                {s.meta !== undefined && (
                  <text
                    x={node.metaX}
                    y={node.metaY}
                    textAnchor="end"
                    className="fan-meta fill-muted"
                  >
                    {s.meta}
                  </text>
                )}
                {s.meta === undefined && s.latencyMs !== undefined && (
                  <text
                    x={node.metaX}
                    y={node.metaY}
                    textAnchor="end"
                    className="fan-meta fill-muted"
                  >
                    {s.cached ? "cached " : ""}
                    {formatLatency(s.latencyMs)}
                  </text>
                )}
              </g>
            );
          })}

          {/* The envelope: one answer. */}
          <g
            ref={envelopeRef}
            style={{ opacity: 0 }}
          >
            <rect
              x={geometry.envelope.x}
              y={geometry.envelope.y}
              width={geometry.envelope.w}
              height={geometry.envelope.h}
              rx={4}
              className="fan-envelope"
            />
            <text
              x={geometry.envelope.labelX}
              y={geometry.envelope.labelY}
              textAnchor="middle"
              className="fan-label fill-ink"
            >
              results[]
            </text>
            <text
              x={geometry.envelope.subX}
              y={geometry.envelope.subY}
              textAnchor="middle"
              className="fan-meta fill-muted"
            >
              {`${services.length} gathered`}
            </text>
          </g>
        </svg>
      </div>

      {caption && (
        <figcaption className="label-wire mt-3">{caption}</figcaption>
      )}
    </figure>
  );
}
