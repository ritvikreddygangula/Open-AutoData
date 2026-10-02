import { ArrowRight, ArrowUpRight, GithubLogo } from "@phosphor-icons/react/ssr";
import { PAPER_BLOG, REPO } from "@/lib/content";
import Magnetic from "./Magnetic";
import PipelineReplay from "./PipelineReplay";
import Reveal from "./Reveal";
import { Logo, Mark } from "./ui";

const NAV = [
  ["Method", "#method"],
  ["Pipeline", "#pipeline"],
  ["Models", "#models"],
  ["Results", "#results"],
  ["Install", "#install"],
];

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-ink/70 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center justify-between px-4 md:px-8">
        <a href="#top" className="flex items-center gap-2 text-fg" aria-label="OpenAutodata home">
          <Mark className="size-5" />
          <span className="text-[15px] font-semibold tracking-tight">OpenAutodata</span>
        </a>
        <nav className="hidden items-center gap-1 md:flex" aria-label="Sections">
          {NAV.map(([label, href]) => (
            <a key={href} href={href} className="rounded-full px-3.5 py-1.5 text-sm text-mute transition-colors hover:bg-white/5 hover:text-fg">
              {label}
            </a>
          ))}
        </nav>
        <a
          href={REPO}
          className="flex items-center gap-2 rounded-full border border-line-2 px-3.5 py-1.5 text-sm text-fg transition hover:bg-white/5 active:scale-[0.98]"
        >
          <GithubLogo size={16} weight="bold" />
          <span>GitHub</span>
        </a>
      </div>
    </header>
  );
}

const STATS = [
  { v: "1.9 → 34", u: "pt", l: "Weak/strong gap, single-shot vs agentic, in Meta's paper" },
  { v: "5", u: "models", l: "Every one open-weight, from five labs" },
  { v: "6", u: "answers", l: "Graded per question: 3 weak, 3 strong, rubric by rubric" },
  { v: "0", u: "labels", l: "Human annotation required to ship a dataset" },
];

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      <div className="grid-bg pointer-events-none absolute inset-0" aria-hidden />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-40 right-[-10%] size-[720px] rounded-full bg-signal/[0.07] blur-[120px]"
      />
      <div className="relative mx-auto grid max-w-[1400px] grid-cols-1 gap-14 px-4 pt-16 pb-12 md:px-8 md:pt-24 lg:min-h-[calc(100dvh-3.5rem)] lg:grid-cols-[1.02fr_1fr] lg:items-center lg:gap-16">
        <div className="min-w-0">
          <Reveal>
            <a
              href={PAPER_BLOG}
              className="group inline-flex items-center gap-2.5 rounded-full border border-line bg-white/[0.03] py-1.5 pr-3.5 pl-2 text-[13px] text-mute transition hover:border-line-2 hover:text-fg"
            >
              <span className="grid size-6 place-items-center rounded-full bg-white/[0.06] text-fg">
                <Logo name="meta" color className="size-3.5" />
              </span>
              Built on Meta FAIR&apos;s AutoData research
              <ArrowUpRight size={13} weight="bold" className="transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
          </Reveal>

          <Reveal delay={0.08}>
            <h1 className="mt-8 text-[2.75rem] leading-[0.98] font-medium tracking-tighter text-fg sm:text-6xl xl:text-7xl">
              Training data
              <br />
              <span className="text-mute">that has to</span> earn
              <br />
              its place.
            </h1>
          </Reveal>

          <Reveal delay={0.16}>
            <p className="mt-7 max-w-[54ch] text-base leading-relaxed text-mute md:text-lg">
              OpenAutodata runs Meta&apos;s <span className="text-fg">Agentic Self-Instruct</span> loop on open-weight models. A question
              ships only when a 3B model fails it and a strong model solves it. Everything else gets rewritten or thrown out.
            </p>
          </Reveal>

          <Reveal delay={0.24}>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Magnetic
                href="#install"
                className="group inline-flex items-center gap-2 rounded-full bg-signal px-5 py-3 text-sm font-semibold text-signal-ink transition-[filter] hover:brightness-110 active:scale-[0.98]"
              >
                Run it yourself
                <ArrowRight size={16} weight="bold" className="transition group-hover:translate-x-0.5" />
              </Magnetic>
              <a
                href="#method"
                className="inline-flex items-center gap-2 rounded-full border border-line-2 px-5 py-3 text-sm font-medium text-fg transition hover:bg-white/5 active:scale-[0.98]"
              >
                See the math gate
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.32}>
            <ul className="mt-10 flex flex-wrap gap-x-5 gap-y-2 font-mono text-[11px] uppercase tracking-[0.16em] text-dim">
              <li>Best Open-Source AI Project</li>
              <li aria-hidden>/</li>
              <li>Snowflake track</li>
              <li aria-hidden>/</li>
              <li>MIT licensed</li>
            </ul>
          </Reveal>
        </div>

        <Reveal delay={0.2} y={28} className="min-w-0">
          <PipelineReplay />
        </Reveal>
      </div>

      <div className="relative mx-auto max-w-[1400px] px-4 pb-20 md:px-8">
        <dl className="grid grid-cols-2 border-t border-line lg:grid-cols-4">
          {STATS.map((s, i) => (
            <Reveal key={s.l} delay={0.05 * i} className={`border-line py-7 pr-6 ${i % 2 ? "pl-6" : ""} ${i > 0 ? "lg:border-l lg:pl-6" : ""} ${i % 2 ? "border-l" : ""} ${i < 2 ? "border-b lg:border-b-0" : ""}`}>
              <dt className="sr-only">{s.l}</dt>
              <dd>
                <div className="font-mono text-3xl tracking-tight text-fg tabular-nums md:text-4xl">
                  {s.v}
                  <span className="ml-1.5 text-sm text-dim">{s.u}</span>
                </div>
                <p className="mt-2 max-w-[28ch] text-sm leading-snug text-mute">{s.l}</p>
              </dd>
            </Reveal>
          ))}
        </dl>
      </div>
    </section>
  );
}
