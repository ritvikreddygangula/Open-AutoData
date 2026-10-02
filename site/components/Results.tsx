"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { CaretDown } from "@phosphor-icons/react";
import { FAILURE_LABEL, latestRun, useJson, type RawRecord, type Traj } from "@/lib/data";
import { DemoBadge, GapMeter, Logo, StatusPill } from "./ui";

const spring = { type: "spring", stiffness: 100, damping: 20 } as const;

export default function Results() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1fr_1.15fr]">
        <PaperBars />
        <OurBenchmark />
      </div>
      <BenchmarkChart />
      <RunLog />
    </div>
  );
}

function Bar({ label, value, max, accent, note }: { label: string; value: number; max: number; accent?: boolean; note: string }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-sm text-fg">{label}</span>
        <span className={`font-mono text-2xl tabular-nums ${accent ? "text-signal" : "text-mute"}`}>{value}</span>
      </div>
      <div className="mt-2.5 h-2.5 overflow-hidden rounded-full bg-white/[0.05]">
        <motion.div
          className={`h-full origin-left rounded-full ${accent ? "bg-signal" : "bg-white/30"}`}
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: value / max }}
          viewport={{ once: true }}
          transition={{ ...spring, delay: 0.2 }}
        />
      </div>
      <p className="mt-2 font-mono text-[11px] text-dim">{note}</p>
    </div>
  );
}

function PaperBars() {
  return (
    <div className="rounded-[1.75rem] border border-line bg-ink-2 p-6 md:p-8">
      <div className="flex items-center gap-2.5">
        <Logo name="meta" className="size-4 text-fg" />
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-dim">Reference · Meta FAIR, AutoData</p>
      </div>
      <p className="mt-4 text-xl font-medium tracking-tight text-fg">Weak/strong gap, in points</p>
      <div className="mt-8 space-y-7">
        <Bar label="CoT Self-Instruct" value={1.9} max={40} note="single-shot generation" />
        <Bar label="Agentic Self-Instruct" value={31.4} max={40} accent note="the loop OpenAutodata implements" />
      </div>
    </div>
  );
}

// First blind A/B run (scripts by Person 3). Small sample: read it as a smoke test, not a result.
const FIRST_RUN = { pairs: 2, baseline: 2.5, openautodata: 6.0, preferred: 2, harder: 2, moreValid: 0 };

function OurBenchmark() {
  const r = FIRST_RUN;
  return (
    <div className="rounded-[1.75rem] border border-line bg-ink-2 p-6 md:p-8">
      <div className="flex items-center gap-2.5">
        <Logo name="qwen" className="size-4 text-fg" />
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-dim">Ours · blind A/B, Qwen3.8 judge</p>
      </div>
      <p className="mt-4 text-xl font-medium tracking-tight text-fg">Same SEC chunks. Single-shot vs OpenAutodata.</p>
      <div className="mt-8 space-y-7">
        <Bar label="Single-shot baseline" value={r.baseline} max={10} note="difficulty, 1-10, independent judge" />
        <Bar label="OpenAutodata" value={r.openautodata} max={10} accent note={`+${(r.openautodata - r.baseline).toFixed(1)} harder`} />
      </div>
      <p className="mt-6 text-sm leading-relaxed text-mute">
        The judge picked OpenAutodata as harder in <span className="font-mono text-signal">{r.harder} of {r.pairs}</span> pairs and preferred
        it overall in <span className="font-mono text-signal">{r.preferred} of {r.pairs}</span>, but rated it more valid in{" "}
        <span className="font-mono text-fg">{r.moreValid} of {r.pairs}</span>.
      </p>
      <p className="mt-3 font-mono text-[11px] text-dim">First run · only {r.pairs} pairs judged · a larger run is next</p>
    </div>
  );
}

function BenchmarkChart() {
  return (
    <figure className="overflow-hidden rounded-[1.75rem] border border-line bg-ink-2 p-3 md:p-4">
      <a href="/benchmark.png" target="_blank" rel="noreferrer" aria-label="Open the benchmark chart full size">
        {/* eslint-disable-next-line @next/next/no-img-element -- static export, no image optimizer */}
        <img
          src="/benchmark.png"
          alt="Benchmark: difficulty 2.5 for single-shot baseline vs 6.0 for OpenAutodata; blind judge preferred OpenAutodata in 100% of pairs, harder in 100%, more valid in 0%; 2 pairs judged."
          width={1600}
          height={727}
          className="h-auto w-full rounded-[1.25rem]"
        />
      </a>
      <figcaption className="px-2 pt-3 font-mono text-[11px] text-dim">
        Blind A/B on 2 SEC chunks. Baseline items have no rubric, so they are compared by the judge only.
      </figcaption>
    </figure>
  );
}

function RunLog() {
  const res = useJson<RawRecord[]>("/data/trajectories.json", 5000);
  const rows = useMemo(() => (res.state === "ready" ? latestRun(res.data) : []), [res]);
  const [open, setOpen] = useState<string | null>(null);

  const accepted = rows.filter((r) => r.status === "ACCEPTED");
  const chunks = new Set(rows.map((r) => r.chunk_id)).size;
  const meanGap = accepted.length ? accepted.reduce((a, r) => a + (r.gap ?? 0), 0) / accepted.length : 0;
  const stats = [
    { l: "Rounds logged", v: String(rows.length) },
    { l: "Accepted pairs", v: `${accepted.length} of ${chunks} chunks` },
    { l: "Rounds per accepted pair", v: accepted.length ? (rows.length / accepted.length).toFixed(1) : "n/a" },
    { l: "Mean accepted gap", v: accepted.length ? `+${meanGap.toFixed(1)}` : "n/a" },
  ];

  return (
    <div className="overflow-hidden rounded-[1.75rem] border border-line bg-ink-2">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-6 py-5 md:px-8">
        <div className="flex items-center gap-3">
          <span className="size-2 animate-breathe rounded-full bg-signal" />
          <p className="text-[15px] font-medium text-fg">Run log</p>
          <span className="font-mono text-[11px] text-dim">
            {rows[0]?.run_id && !rows[0]?.demo ? `${rows[0].run_id} · ` : ""}data/trajectories.json · polling every 5s
          </span>
        </div>
        {rows.some((r) => r.demo) && <DemoBadge />}
      </div>

      <dl className="grid grid-cols-2 divide-line border-b border-line md:grid-cols-4 md:divide-x">
        {stats.map((s) => (
          <div key={s.l} className="px-6 py-5 md:px-8">
            <dt className="font-mono text-[11px] uppercase tracking-[0.14em] text-dim">{s.l}</dt>
            <dd className="mt-1.5 font-mono text-2xl text-fg tabular-nums">{s.v}</dd>
          </div>
        ))}
      </dl>

      {res.state === "loading" && <div className="h-40 animate-pulse bg-white/[0.02]" />}
      {res.state === "error" && (
        <p className="px-8 py-12 text-sm text-mute">
          No trajectories yet. Run <code className="font-mono text-fg">python -m src.agent_graph</code> and rows appear here live.
        </p>
      )}
      {res.state === "ready" && rows.length === 0 && <p className="px-8 py-12 text-sm text-mute">The run log is empty. The first round lands here within seconds of starting the pipeline.</p>}

      <ul className="divide-y divide-line">
        {rows.map((r) => {
          const id = `${r.chunk_id}-${r.round_num}`;
          return <Row key={id} r={r} open={open === id} onToggle={() => setOpen(open === id ? null : id)} />;
        })}
      </ul>
    </div>
  );
}

function Row({ r, open, onToggle }: { r: Traj; open: boolean; onToggle: () => void }) {
  return (
    <li>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="grid w-full cursor-pointer grid-cols-[1fr_auto] items-center gap-x-4 gap-y-3 px-6 py-4 text-left transition-colors hover:bg-white/[0.02] md:grid-cols-[minmax(0,1.6fr)_120px_minmax(180px,1fr)_70px_24px] md:px-8"
      >
        <span className="min-w-0">
          <span className="block truncate text-[15px] text-fg">{r.question || "No question produced"}</span>
          <span className="mt-0.5 block font-mono text-[11px] text-dim">
            {r.source ?? `chunk ${r.chunk_id}`} · round {r.round_num}
          </span>
        </span>
        <span className="justify-self-end md:justify-self-start">
          <StatusPill status={r.status} />
        </span>
        <span className="col-span-2 md:col-span-1">
          {r.strongRan ? (
            <GapMeter weak={r.weakAvg} strong={r.strongAvg} pass={r.status === "ACCEPTED"} />
          ) : (
            <span className={`font-mono text-[11px] ${r.isError ? "text-fail" : "text-dim"}`}>
              {r.isError ? "error · chunk ended" : `${r.failure_mode ? FAILURE_LABEL[r.failure_mode] : "no scores"} · not solved`}
            </span>
          )}
        </span>
        <span className={`hidden text-right font-mono text-sm tabular-nums md:block ${r.status === "ACCEPTED" ? "text-signal" : "text-mute"}`}>
          {r.gap == null ? "n/a" : `${r.gap >= 0 ? "+" : ""}${r.gap.toFixed(1)}`}
        </span>
        <CaretDown size={16} className={`hidden text-dim transition-transform duration-300 md:block ${open ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0, transition: { duration: 0.18 } }}
            transition={spring}
            className="overflow-hidden"
          >
            <div className="grid gap-8 px-6 pt-2 pb-8 md:grid-cols-2 md:px-8">
              <div className="space-y-5">
                <Field k="Context (all the solvers see)" v={r.context} />
                <Field k="Question" v={r.question} />
                <Field k="Reference answer (judge never sees this)" v={r.reference_answer} />
                <Field k="Why it failed" v={r.fail_reason ?? undefined} />
                <Field k="Judge notes" v={r.judge_feedback ?? undefined} />
              </div>
              <div className="space-y-5">
                {r.rubric && (
                  <div>
                    <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-dim">Rubric</p>
                    <ul className="mt-2 divide-y divide-line rounded-xl border border-line">
                      {r.rubric.map((c) => (
                        <li key={c.criterion} className="flex justify-between gap-4 px-4 py-2.5 text-sm text-mute">
                          <span>{c.criterion}</span>
                          <span className="font-mono text-fg">{c.weight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4 font-mono text-sm">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.14em] text-dim">Weak runs</p>
                    <p className="mt-1 text-fg">{r.weak.length ? r.weak.join(" · ") : "skipped"}</p>
                  </div>
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.14em] text-dim">Strong runs</p>
                    <p className="mt-1 text-signal">{r.strongRan ? r.strong.join(" · ") : "skipped"}</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}

function Field({ k, v }: { k: string; v?: string | null }) {
  if (!v) return null;
  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-dim">{k}</p>
      <p className="mt-1.5 text-[15px] leading-relaxed text-fg/90">{v}</p>
    </div>
  );
}
