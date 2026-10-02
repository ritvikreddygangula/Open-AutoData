"use client";

import { memo, useEffect, useMemo, useState } from "react";
import { AnimatePresence, animate, motion, useMotionValue, useReducedMotion, useTransform } from "motion/react";
import { FAILURE_LABEL, latestRun, useJson, type RawRecord, type Traj } from "@/lib/data";
import { GATE } from "@/lib/gate";
import { DemoBadge, GapMeter, Logo, Mark, StatusPill } from "./ui";

const spring = { type: "spring", stiffness: 100, damping: 20 } as const;

type Stage = { key: string; logo?: string; role: string; model: string };
const STAGES: Stage[] = [
  { key: "chunk", logo: "snowflake", role: "Chunk", model: "Snowflake · SEC 10-Q" },
  { key: "challenger", logo: "zhipu", role: "Challenger", model: "GLM-5.3" },
  { key: "verifier", logo: "nvidia", role: "Quality check", model: "Nemotron 3 Super" },
  { key: "weak", logo: "meta", role: "Weak ×3", model: "Llama 3.2 3B · SLM" },
  { key: "strong", logo: "deepseek", role: "Strong ×3", model: "DeepSeek V4.1 Flash" },
  { key: "judge", logo: "nvidia", role: "Rubric judge", model: "Nemotron 3 Super" },
  { key: "gate", role: "Gate", model: "node_evaluate" },
];

function durations(q: string) {
  return [900, Math.min(3200, 600 + q.length * 22), 1300, 1500, 1500, 1500, 2600];
}

export default function PipelineReplay() {
  const res = useJson<RawRecord[]>("/data/trajectories.json", 5000);
  const reduce = useReducedMotion();
  const records = useMemo(() => (res.state === "ready" ? latestRun(res.data) : []), [res]);
  const [idx, setIdx] = useState(0);
  const [phase, setPhase] = useState(0);

  const rec = records.length ? records[idx % records.length] : undefined;

  useEffect(() => {
    if (!rec) return;
    const d = durations(rec.question ?? "");
    const t = setTimeout(
      () => {
        if (phase < STAGES.length - 1) setPhase(phase + 1);
        else {
          setPhase(0);
          setIdx((i) => i + 1);
        }
      },
      reduce ? 2500 : d[phase],
    );
    return () => clearTimeout(t);
  }, [phase, rec, reduce]);

  return (
    <div className="relative rounded-[1.75rem] border border-line bg-ink-2/80 p-1.5 shadow-[0_40px_80px_-30px_rgba(0,0,0,0.8)] backdrop-blur-xl">
      <div className="rounded-[1.4rem] border border-white/[0.06] bg-ink-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
        <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-3.5">
          <div className="flex min-w-0 items-center gap-2.5 font-mono text-[11px] uppercase tracking-[0.16em] text-mute">
            <span className="relative flex size-2">
              <span className="absolute inset-0 animate-breathe rounded-full bg-signal" />
            </span>
            <span className="shrink-0 text-fg">Live replay</span>
            <span className="truncate text-dim normal-case tracking-normal">{rec ? rec.source ?? `${rec.run_id ? `${rec.run_id} · ` : ""}chunk ${rec.chunk_id}` : "waiting for trajectories"}</span>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {rec?.demo && <DemoBadge />}
            {rec && (
              <span className="font-mono text-[11px] text-dim">
                round <span className="text-fg">{rec.round_num}</span>/{GATE.maxRounds}
              </span>
            )}
          </div>
        </header>

        {res.state === "loading" && <ReplaySkeleton />}
        {res.state === "error" && (
          <div className="px-5 py-10 text-sm text-mute">
            No run log yet. Start the pipeline with <code className="font-mono text-fg">python -m src.agent_graph</code> and this panel picks it up.
          </div>
        )}
        {rec && <Timeline rec={rec} phase={phase} />}
      </div>
    </div>
  );
}

const Timeline = memo(function Timeline({ rec, phase }: { rec: Traj; phase: number }) {
  return (
    <ol className="relative px-3 py-3">
      {/* rail */}
      <div className="absolute top-8 bottom-8 left-[44px] w-px bg-line" aria-hidden />
      <motion.div
        aria-hidden
        className="absolute top-8 bottom-8 left-[44px] w-px origin-top bg-signal/70"
        animate={{ scaleY: phase / (STAGES.length - 1) }}
        transition={spring}
      />
      {STAGES.map((s, i) => {
        const reached = i <= phase;
        const active = i === phase;
        return (
          <li key={s.key} className="relative">
            {active && (
              <motion.div layoutId="replay-active" transition={spring} className="absolute inset-0 rounded-2xl bg-white/[0.035] ring-1 ring-inset ring-white/[0.06]" />
            )}
            <div className={`relative grid grid-cols-[48px_1fr] gap-x-2 px-2 py-2.5 transition-opacity duration-500 ${reached ? "opacity-100" : "opacity-30"}`}>
              <div className="relative z-10 grid size-9 place-items-center justify-self-center rounded-xl border border-line bg-ink-3 text-fg">
                {s.logo ? <Logo name={s.logo} className="size-[18px]" /> : <Mark className="size-[18px]" />}
              </div>
              <div className="min-w-0 self-center">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="text-sm font-medium text-fg">{s.role}</span>
                  <span className="truncate font-mono text-[11px] text-dim">{s.model}</span>
                </div>
                <StageBody stage={s.key} rec={rec} reached={reached} active={active} />
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
});

function Skipped({ why }: { why: string }) {
  return <p className="mt-0.5 font-mono text-[11px] text-dim">skipped · {why}</p>;
}

function StageBody({ stage, rec, reached, active }: { stage: string; rec: Traj; reached: boolean; active: boolean }) {
  if (!reached) return null;
  const qvFailed = rec.failure_mode === "FAILED_QV";
  // After an error, stages that produced nothing show "skipped" instead of a fake pass.
  const errSkip = rec.isError && !rec.weak.length;
  switch (stage) {
    case "chunk":
      return <p className="mt-0.5 font-mono text-[11px] text-dim">chunk_id {rec.chunk_id} · Results of Operations</p>;
    case "challenger":
      return rec.question ? <Typed key={`${rec.chunk_id}-${rec.round_num}`} text={rec.question} typing={active} /> : <Skipped why="error" />;
    case "verifier":
      if (errSkip && !qvFailed) return <Skipped why="error" />;
      return qvFailed ? (
        <p className="mt-1 line-clamp-2 text-[13px] leading-snug text-fail">{rec.verifier_feedback ?? "failed quality check"}</p>
      ) : (
        <p className="mt-0.5 font-mono text-[11px] text-signal">pass · no leakage · tests reasoning</p>
      );
    case "weak":
      return rec.weak.length ? <Scores scores={rec.weak} avg={rec.weakAvg} tone="weak" /> : <Skipped why={qvFailed ? "failed quality check" : "error"} />;
    case "strong":
      if (rec.strongRan) return <Scores scores={rec.strong} avg={rec.strongAvg} tone="strong" />;
      return <Skipped why={qvFailed ? "failed quality check" : "error"} />;
    case "judge":
      return rec.judge_feedback ? (
        <p className="mt-1 line-clamp-2 text-[13px] leading-snug text-mute">{rec.judge_feedback}</p>
      ) : (
        <Skipped why="nothing to grade" />
      );
    case "gate":
      return (
        <div className="mt-1.5">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <StatusPill status={rec.status} />
              {rec.failure_mode && <span className="font-mono text-[11px] text-dim">{FAILURE_LABEL[rec.failure_mode]}</span>}
              {rec.isError && <span className="font-mono text-[11px] text-fail">error</span>}
            </div>
            {rec.gap != null && (
              <span className="font-mono text-xs text-mute">
                gap <span className={rec.gap >= GATE.gapMin ? "text-signal" : "text-fail"}>{rec.gap >= 0 ? "+" : ""}{rec.gap.toFixed(1)}</span>
              </span>
            )}
          </div>
          {rec.isError && <p className="mt-1.5 line-clamp-2 font-mono text-[11px] text-dim">{rec.fail_reason}</p>}
          {rec.strongRan && (
            <div className="mt-2">
              <GapMeter weak={rec.weakAvg} strong={rec.strongAvg} pass={rec.status === "ACCEPTED"} />
            </div>
          )}
        </div>
      );
  }
  return null;
}

function Typed({ text, typing }: { text: string; typing: boolean }) {
  const reduce = useReducedMotion();
  const count = useMotionValue(typing && !reduce ? 0 : text.length);
  const shown = useTransform(count, (v) => text.slice(0, Math.round(v)));
  useEffect(() => {
    if (!typing || reduce) return;
    const c = animate(count, text.length, { duration: Math.min(2.8, text.length * 0.02), ease: "linear" });
    return () => c.stop();
  }, [typing, reduce, text, count]);
  return (
    <p className="mt-1 text-[13px] leading-snug text-fg/90">
      <motion.span>{shown}</motion.span>
      {typing && <span className="ml-0.5 inline-block h-3.5 w-[7px] translate-y-0.5 animate-blink bg-signal" />}
    </p>
  );
}

function Scores({ scores, avg, tone }: { scores: number[]; avg: number; tone: "weak" | "strong" }) {
  return (
    <div className="mt-1.5 flex items-center gap-1.5">
      <AnimatePresence>
        {scores.map((s, i) => (
          <motion.span
            key={i}
            initial={{ opacity: 0, scale: 0.6, y: 4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ ...spring, delay: i * 0.18 }}
            className={`rounded-md px-2 py-0.5 font-mono text-xs tabular-nums ring-1 ring-inset ${
              s === 0 ? "bg-fail/10 text-fail ring-fail/30" : tone === "strong" ? "bg-signal/10 text-signal ring-signal/25" : "bg-white/[0.06] text-fg ring-white/10"
            }`}
          >
            {s}
          </motion.span>
        ))}
      </AnimatePresence>
      <span className="ml-auto font-mono text-[11px] text-dim">
        avg <span className="text-fg tabular-nums">{avg.toFixed(1)}</span>
      </span>
    </div>
  );
}

function ReplaySkeleton() {
  return (
    <div className="space-y-3 p-5" aria-label="Loading run log">
      {STAGES.map((s) => (
        <div key={s.key} className="flex items-center gap-3">
          <div className="size-9 rounded-xl bg-white/[0.04]" />
          <div className="relative h-3 flex-1 overflow-hidden rounded bg-white/[0.04]">
            <div className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
          </div>
        </div>
      ))}
    </div>
  );
}
