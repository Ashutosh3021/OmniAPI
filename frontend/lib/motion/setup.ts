import { gsap } from "gsap";
import { onPage, onScroll } from "@/lib/engine";

/**
 * The concept driver.
 *
 * One variable: scroll velocity. It drives the pulse that travels every spine on
 * the page, so the system breathes harder while you move and settles when you
 * stop. Nothing else animates on its own, and nothing animates twice.
 */
export function startConcept() {
  onPage(() => {
    const spines = Array.from(
      document.querySelectorAll<SVGLineElement | SVGPathElement>("[data-pulse]")
    );
    if (!spines.length) return;

    const pulses = spines.map((el) => {
      const length = 14;
      gsap.set(el, { strokeDasharray: `${length}`, strokeDashoffset: length });
      return gsap.fromTo(
        el,
        { strokeDashoffset: length },
        { strokeDashoffset: -length, duration: 2.6, ease: "none", repeat: -1 }
      );
    });

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
