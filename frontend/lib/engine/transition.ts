// Page transitions. The concept's transition: a signal sweeps across the panel.
// The panel wipes in from the left behind it, then wipes out to the right on the
// way in, so the new page is revealed by the same gesture that covered the old one.
import { gsap } from "gsap";
import { ease, prefersReducedMotion } from "./env";

export type Transition = {
  leave: (curtain: HTMLElement) => Promise<unknown> | gsap.core.Animation;
  enter: (curtain: HTMLElement) => Promise<unknown> | gsap.core.Animation;
};

const sweep: Transition = {
  leave: (c) => {
    const panel = c.querySelector<HTMLElement>(".curtain__panel");
    const line = c.querySelector<HTMLElement>(".curtain__sweep");
    return gsap
      .timeline()
      .set(c, { autoAlpha: 1 })
      .set(panel, { scaleX: 0, transformOrigin: "left center" })
      .set(line, { xPercent: -30, opacity: 0 })
      .to(panel, { scaleX: 1, duration: 0.42, ease: ease.inOut })
      .to(line, { xPercent: 125, opacity: 1, duration: 0.52, ease: ease.inOut }, 0.04)
      .to(line, { opacity: 0, duration: 0.14 }, 0.42);
  },
  enter: (c) => {
    const panel = c.querySelector<HTMLElement>(".curtain__panel");
    const line = c.querySelector<HTMLElement>(".curtain__sweep");
    return gsap
      .timeline()
      .set(panel, { scaleX: 1, transformOrigin: "right center" })
      .set(line, { xPercent: 125, opacity: 0 })
      .to(line, { xPercent: -30, opacity: 1, duration: 0.52, ease: ease.inOut }, 0)
      .to(panel, { scaleX: 0, duration: 0.42, ease: ease.inOut }, 0.1)
      .to(line, { opacity: 0, duration: 0.14 }, 0.42)
      .set(c, { autoAlpha: 0 });
  },
};

const reduced: Transition = {
  leave: (c) =>
    gsap.timeline().set(c, { autoAlpha: 1 }).fromTo(c, { opacity: 0 }, { opacity: 1, duration: 0.18 }),
  enter: (c) => gsap.to(c, { autoAlpha: 0, duration: 0.18 }),
};

let current: Transition = sweep;

export const setTransition = (t: Transition) => {
  current = t;
};

const pick = () => (prefersReducedMotion() ? reduced : current);
const curtain = () => document.getElementById("curtain") as HTMLElement;

export const playLeave = () => Promise.resolve(pick().leave(curtain()));
export const playEnter = () => Promise.resolve(pick().enter(curtain()));
