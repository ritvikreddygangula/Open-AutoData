import { ArrowUpRight, GithubLogo } from "@phosphor-icons/react/ssr";
import { AUTHORS, MARQUEE, MODELS, PAPER_ARXIV, PAPER_BLOG, REPO, STACK } from "@/lib/content";
import Reveal from "./Reveal";
import { Logo, Mark, SectionHead } from "./ui";

export function Marquee() {
  const row = [...MARQUEE, ...MARQUEE];
  return (
    <div className="relative overflow-hidden border-y border-line bg-ink-2 py-5" aria-label={MARQUEE.join(", ")}>
      <div className="flex w-max animate-marquee gap-10 whitespace-nowrap" aria-hidden>
        {row.map((w, i) => (
          <span key={i} className="flex items-center gap-10 font-mono text-sm uppercase tracking-[0.2em] text-dim">
            {w}
            <span className="size-1.5 rounded-full bg-signal/70" />
          </span>
        ))}
      </div>
      <div className="pointer-events-none absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-ink-2 to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-ink-2 to-transparent" />
    </div>
  );
}

const FAILURES = [
  { tag: "Too easy", body: "The model already knows the answer. It trains on nothing.", example: "“What was Q1 revenue?” Pure lookup." },
  { tag: "Unanswerable", body: "The source text cannot support the answer, so the model learns to guess.", example: "Ambiguous base for a 97/3 split." },
  { tag: "Wrong key", body: "The reference answer itself is off, and fine-tuning bakes the error in.", example: "Gross price read as net sales." },
];

export function Problem() {
  return (
    <section className="mx-auto max-w-[1400px] px-4 py-24 md:px-8 md:py-28">
      <SectionHead n="01" kicker="The problem" title={<>Most synthetic data is <span className="text-mute">never checked.</span></>}>
        Big labs pay human annotators to write and review fine-tuning pairs. Everyone else prompts an LLM and ships whatever comes
        back. Teams report row counts. Nobody reports a pass rate.
      </SectionHead>

      <div className="mt-16 grid gap-10 md:grid-cols-[180px_1fr] md:gap-10">
        <div className="hidden md:block" />
        <ol className="divide-y divide-line border-y border-line">
          {FAILURES.map((f, i) => (
            <Reveal as="li" key={f.tag} delay={i * 0.06} className="group grid gap-3 py-7 md:grid-cols-[220px_1fr_260px] md:items-baseline md:gap-8">
                <span className="flex items-center gap-3 font-mono text-xs uppercase tracking-[0.18em] text-fail">
                  <span className="text-dim">0{i + 1}</span> {f.tag}
                </span>
                <p className="text-lg leading-snug text-fg md:text-xl">{f.body}</p>
                <p className="font-mono text-xs text-dim md:text-right">{f.example}</p>
            </Reveal>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Models() {
  return (
    <section id="models" className="mx-auto max-w-[1400px] scroll-mt-16 px-4 py-24 md:px-8 md:py-28">
      <SectionHead n="04" kicker="The agents" title={<>Five open-weight models. <span className="text-mute">Six roles.</span></>}>
        Different labs, different sizes, on purpose. The weak solver is a small language model, 3B parameters, small enough to
        struggle. Every other role runs a large model. The benchmark judge comes from a separate family so the pipeline never
        grades its own homework.
      </SectionHead>

      <div className="mt-16 grid gap-10 md:grid-cols-[180px_1fr]">
        <div className="hidden md:block" />
        <ul className="border-t border-line">
          {MODELS.map((m, i) => (
            <Reveal as="li" key={m.role} delay={i * 0.05} className="group grid grid-cols-[56px_1fr] gap-x-5 gap-y-3 border-b border-line py-7 transition-colors hover:bg-white/[0.02] md:grid-cols-[72px_250px_1fr_auto] md:items-center md:gap-x-8 md:px-4">
              <div className="grid size-14 place-items-center rounded-2xl border border-line bg-ink-2 text-fg transition group-hover:border-line-2 md:size-16">
                <Logo name={m.logo} color className="size-7" />
              </div>
              <div>
                <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-dim">{m.role}</p>
                <a href={m.hf} className="mt-1 inline-flex items-center gap-1.5 text-xl font-medium tracking-tight text-fg underline-offset-4 hover:underline">
                  {m.model} <ArrowUpRight size={14} weight="bold" className="text-dim" />
                </a>
                <p className="text-sm text-mute">{m.vendor}</p>
              </div>
              <div className="col-span-2 md:col-span-1">
                <p className="max-w-[56ch] text-[15px] leading-relaxed text-mute">{m.job}</p>
                <a href={m.licenseUrl} className="mt-2 inline-block font-mono text-[11px] text-dim underline decoration-line-2 underline-offset-4 transition hover:text-fg">
                  License: {m.license}
                </a>
              </div>
              <span
                className={`col-span-2 w-fit rounded-full px-3 py-1 font-mono text-[11px] uppercase tracking-wider ring-1 ring-inset md:col-span-1 ${
                  m.size === "SLM" ? "bg-signal/10 text-signal ring-signal/30" : "text-mute ring-line-2"
                }`}
                title={m.size === "SLM" ? "Small language model: 10B parameters or fewer" : "Large language model"}
              >
                {m.size} · {m.params}
              </span>
            </Reveal>
          ))}
        </ul>
      </div>

      <div className="mt-14 grid gap-6 md:grid-cols-[180px_1fr]">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-dim">Runs on</p>
        <ul className="flex flex-wrap items-center gap-x-10 gap-y-5">
          {STACK.map((s) => (
            <li key={s.name} className="group flex items-center gap-2.5 text-mute transition-colors hover:text-fg">
              <Logo name={s.logo} color className="size-6" />
              <span className="text-sm font-medium">{s.name}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function Research() {
  return (
    <section className="relative overflow-hidden border-y border-line bg-ink-2">
      <div className="mx-auto grid max-w-[1400px] gap-12 px-4 py-24 md:px-8 md:py-32 lg:grid-cols-[1fr_1.1fr] lg:items-end">
        <Reveal>
          <div className="flex items-center gap-3 font-mono text-xs uppercase tracking-[0.18em] text-dim">
            <span className="text-signal">07</span> The research
          </div>
          <h2 className="mt-6 text-3xl leading-[1.05] font-medium tracking-tighter text-fg md:text-5xl">
            Standing on <span className="inline-flex translate-y-1 items-center"><Logo name="meta" className="mx-1 size-8 md:size-11" /></span> Meta FAIR&apos;s
            Agentic Self-Instruct.
          </h2>
        </Reveal>
        <Reveal delay={0.1}>
          <p className="max-w-[60ch] text-base leading-relaxed text-mute md:text-lg">
            AutoData treats data creation as an agent loop: a challenger proposes, a weak and a strong solver attempt, a judge scores
            against a rubric, and the loop revises until the example splits the two solvers. Meta measured a <span className="text-fg">34 point</span> weak/strong gap with this method versus <span className="text-fg">1.9</span> for single-shot CoT Self-Instruct. We rebuilt the loop as an open-source LangGraph harness, swapped in a different open-weight model set, and pointed it at SEC filings in Snowflake.
          </p>
          <p className="mt-6 font-mono text-xs leading-relaxed text-dim">{AUTHORS}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href={PAPER_BLOG} className="inline-flex items-center gap-2 rounded-full border border-line-2 px-4 py-2 text-sm text-fg transition hover:bg-white/5 active:scale-[0.98]">
              Read the blog <ArrowUpRight size={14} weight="bold" />
            </a>
            <a href={PAPER_ARXIV} className="inline-flex items-center gap-2 rounded-full border border-line-2 px-4 py-2 text-sm text-fg transition hover:bg-white/5 active:scale-[0.98]">
              arXiv 2606.25996 <ArrowUpRight size={14} weight="bold" />
            </a>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="mx-auto max-w-[1400px] px-4 pt-20 pb-10 md:px-8">
      <div className="flex flex-col justify-between gap-10 md:flex-row md:items-end">
        <div>
          <div className="flex items-center gap-2.5 text-fg">
            <Mark className="size-7" />
            <span className="text-2xl font-semibold tracking-tight">OpenAutodata</span>
          </div>
          <p className="mt-4 max-w-[44ch] text-sm leading-relaxed text-mute">
            Verified fine-tuning data from any document. Open-weight models, open-source harness, MIT licensed.
          </p>
        </div>
        <a href={REPO} className="inline-flex w-fit items-center gap-2 rounded-full bg-fg px-5 py-3 text-sm font-semibold text-ink transition hover:brightness-90 active:scale-[0.98]">
          <GithubLogo size={16} weight="bold" /> Star on GitHub
        </a>
      </div>
      <div className="mt-16 flex flex-col justify-between gap-3 border-t border-line pt-6 font-mono text-[11px] uppercase tracking-[0.16em] text-dim md:flex-row">
        <span>Hack Day 2026 · Best Open-Source AI Project · Snowflake track</span>
        <span>MIT License</span>
      </div>
    </footer>
  );
}
