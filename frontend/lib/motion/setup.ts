import { gsap } from "gsap";
import { onPage, onScroll, prefersReducedMotion } from "@/lib/engine";

/**
 * The concept driver.
 *
 * One variable: scroll velocity. It drives the pulse that travels every spine on
 * the page and the glow that runs down every rail, so the system breathes harder
 * while you move and settles when you stop. Nothing else animates on its own,
 * and nothing animates twice.
 */
export function startConcept() {
  onPage(() => {
    if (prefersReducedMotion()) return;

    const pulses: gsap.core.Tween[] = [];

    const spines = Array.from(
      document.querySelectorAll<SVGLineElement | SVGPathElement>("[data-pulse]")
    );
    for (const el of spines) {
      const length = 14;
      gsap.set(el, { strokeDasharray: `${length}`, strokeDashoffset: length });
      pulses.push(
        gsap.fromTo(
          el,
          { strokeDashoffset: length },
          {
            strokeDashoffset: -length,
            duration: 2.6,
            ease: "none",
            repeat: -1,
          }
        )
      );
    }

    const rails = Array.from(
      document.querySelectorAll<HTMLElement>("[data-pulse-rail]")
    );
    for (const el of rails) {
      const host = el.parentElement;
      const travel = (host?.offsetHeight ?? 600) + 200;
      pulses.push(
        gsap.fromTo(
          el,
          { y: -200 },
          {
            y: travel,
            duration: 7,
            ease: "none",
            repeat: -1,
            repeatDelay: 0.4,
          }
        )
      );
    }

    if (!pulses.length) return;

    const off = onScroll(({ velocity }) => {
      const scale = 1 + Math.min(Math.abs(velocity) / 45, 2.4);
      pulses.forEach((p) =>
        gsap.to(p, { timeScale: scale, duration: 0.6, overwrite: true })
      );
    });

    return () => {
      off();
      pulses.forEach((p) => p.kill());
    };
  });
}

export function setupMotion() {
  startConcept();
}
