"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check, X } from "@phosphor-icons/react";
import { checkGate } from "@/lib/gate";
import { GapMeter, Logo } from "./ui";

const PRESETS = [
  { name: "Sweet spot", weak: [42, 55, 48], strong: [84, 90, 81] },
  { name: "Too easy", weak: [88, 92, 85], strong: [97, 100, 96] },
  { name: "Broken question", weak: [40, 35, 50], strong: [45, 52, 38] },
  { name: "Lucky weak run", weak: [30, 78, 40], strong: [85, 88, 90] },
  { name: "Weak zeroed", weak: [0, 35, 30], strong: [72, 70, 75] },
];

const spring = { type: "spring", stiffness: 100, damping: 20 } as const;

export default function GateLab() {
  const [weak, setWeak] = useState(PRESETS[0].weak);
  const [strong, setStrong] = useState(PRESETS[0].strong);
  const g = checkGate(weak, strong);
  const verdict = g.pass ? "ACCEPTED" : "REVISE";

  const set = (which: "weak" | "strong", i: number, v: number) => {
    const upd = (xs: number[]) => xs.map((x, j) => (j === i ? v : x));
    if (which === "weak") setWeak(upd);
    else setStrong(upd);
  };

  return (
    <div className="grid overflow-hidden rounded-[1.75rem] border border-line bg-ink-2 lg:grid-cols-[1.25fr_1fr]">
      <div className="border-b border-line p-6 md:p-8 lg:border-r lg:border-b-0">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Presets">
          {PRESETS.map((p) => {
            const on = p.weak.join() === weak.join() && p.strong.join() === strong.join();
            return (
              <button
                key={p.name}
                type="button"
                onClick={() => {
                  setWeak(p.weak);
                  setStrong(p.strong);
                }}
                aria-pressed={on}
                className={`cursor-pointer rounded-full px-3.5 py-1.5 text-[13px] transition active:scale-[0.97] ${
                  on ? "bg-fg text-ink" : "border border-line-2 text-mute hover:text-fg"
                }`}
              >
                {p.name}
              </button>
            );
          })}
        </div>

        <div className="mt-8 space-y-8">
          <Lane title="Weak solver" model="Llama 3.2 3B" logo="meta" scores={weak} onChange={(i, v) => set("weak", i, v)} />
          <Lane title="Strong solver" model="DeepSeek V4.1 Flash" logo="deepseek" scores={strong} onChange={(i, v) => set("strong", i, v)} accent />
        </div>

        <div className="mt-10">
          <div className="mb-2 flex justify-between font-mono text-[11px] uppercase tracking-[0.16em] text-dim">
            <span>Average positions</span>
            <span>0 to 100</span>
          </div>
          <GapMeter weak={g.weakAvg} strong={g.strongAvg} pass={g.pass} />
        </div>
      </div>

      <div className="flex flex-col p-6 md:p-8">
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-dim">node_evaluate</p>
        <ul className="mt-4 divide-y divide-line">
          {g.checks.map((c) => (
            <li key={c.id} className="flex items-center justify-between gap-4 py-3.5">
              <span className="flex items-center gap-3">
                <motion.span
                  key={String(c.pass)}
                  initial={{ scale: 0.4, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={spring}
                  className={`grid size-6 place-items-center rounded-full ${c.pass ? "bg-signal/15 text-signal" : "bg-fail/15 text-fail"}`}
                >
                  {c.pass ? <Check size={13} weight="bold" /> : <X size={13} weight="bold" />}
                  <span className="sr-only">{c.pass ? "pass" : "fail"}</span>
                </motion.span>
                <span className="text-[15px] text-fg">{c.label}</span>
              </span>
              <span className="font-mono text-sm text-mute tabular-nums">{c.detail}</span>
            </li>
          ))}
        </ul>

        <div className="mt-auto pt-8" aria-live="polite">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-dim">Verdict</p>
          <div className="mt-2 flex items-end justify-between gap-4">
            <AnimatePresence mode="wait">
              <motion.p
                key={verdict}
                initial={{ y: 14, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -10, opacity: 0, transition: { duration: 0.15 } }}
                transition={spring}
                className={`text-4xl font-medium tracking-tighter md:text-5xl ${g.pass ? "text-signal" : "text-warn"}`}
              >
                {g.pass ? "Accepted" : "Revise"}
              </motion.p>
            </AnimatePresence>
            <p className="pb-1.5 text-right text-sm text-mute">
              {g.pass ? "Ships to the dataset." : `${g.checks.filter((c) => !c.pass).length} check${g.checks.filter((c) => !c.pass).length > 1 ? "s" : ""} failed. Feedback goes back to the Challenger.`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Lane({
  title,
  model,
  logo,
  scores,
  onChange,
  accent,
}: {
  title: string;
  model: string;
  logo: string;
  scores: number[];
  onChange: (i: number, v: number) => void;
  accent?: boolean;
}) {
  return (
    <fieldset>
      <legend className="flex w-full items-center gap-2.5">
        <Logo name={logo} className="size-4 text-fg" />
        <span className="text-sm font-medium text-fg">{title}</span>
        <span className="font-mono text-[11px] text-dim">{model}</span>
      </legend>
      <div className="mt-3 space-y-1">
        {scores.map((s, i) => (
          <label key={i} className="grid grid-cols-[48px_1fr_36px] items-center gap-3">
            <span className="font-mono text-[11px] text-dim">run {i + 1}</span>
            <input
              type="range"
              min={0}
              max={100}
              value={s}
              onChange={(e) => onChange(i, Number(e.target.value))}
              aria-label={`${title} run ${i + 1} score`}
              style={{ accentColor: accent ? "var(--color-signal)" : "var(--color-fg)" }}
            />
            <span className={`text-right font-mono text-sm tabular-nums ${s === 0 ? "text-fail" : accent ? "text-signal" : "text-fg"}`}>{s}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
