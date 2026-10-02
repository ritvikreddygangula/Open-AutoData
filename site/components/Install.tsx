"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check, Copy, FileArrowDown, Sparkle, Terminal } from "@phosphor-icons/react";
import { REPO } from "@/lib/content";

const TABS = [
  {
    id: "run",
    label: "Run the pipeline",
    icon: Terminal,
    blurb: "Python 3.11+, your own OpenRouter key. Nothing runs on our servers. Snowflake writeback is optional.",
    code: `$ git clone ${REPO} && cd Open-AutoData
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt
$ cp .env.example .env        # set OPEN_ROUTER=sk-or-...
$ python -m src.chunks my_filings.csv   # any CSV with CHUNK_ID, CHUNK_TEXT
$ python -m src.agent_graph             # full loop, lands with feat/agent-graph`,
  },
  {
    id: "site",
    label: "Watch it live",
    icon: Sparkle,
    blurb: "This site reads data/trajectories.json and polls it while the pipeline runs.",
    code: `$ cd site
$ npm install
$ npm run dev          # http://localhost:3000`,
  },
  {
    id: "out",
    label: "Output",
    icon: FileArrowDown,
    blurb: "One record per round in data/trajectories.json. Accepted pairs also land in data/accepted.json and Snowflake.",
    code: `{"chunk_id": "7", "round_num": 2, "status": "ACCEPTED",
 "question": "Valuing the barrels lost at Q1 2025 net revenue per barrel...",
 "reference_answer": "116,000 × $270.64 ≈ $31.4M lost to volume...",
 "rubric": [{"criterion": "Computes the volume effect at about $31.4M", "weight": 5}, ...],
 "weak_attempt_scores": [42.5, 55, 47.5], "weak_score": 48.3,
 "strong_attempt_scores": [85, 90, 80], "strong_score": 85.0,
 "score_gap": 36.7}`,
  },
];

export default function Install() {
  const [tab, setTab] = useState(TABS[0].id);
  const [copied, setCopied] = useState(false);
  const t = TABS.find((x) => x.id === tab)!;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(t.code.replace(/^\$ /gm, "").replace(/\s+#.*$/gm, ""));
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard blocked: the code stays selectable */
    }
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:gap-10">
      <div role="tablist" aria-label="Ways to run OpenAutodata" className="flex flex-col gap-2">
        {TABS.map((x) => {
          const on = x.id === tab;
          const Icon = x.icon;
          return (
            <button
              key={x.id}
              role="tab"
              aria-selected={on}
              aria-controls="install-panel"
              onClick={() => setTab(x.id)}
              className="relative cursor-pointer rounded-2xl px-5 py-4 text-left transition active:scale-[0.99]"
            >
              {on && <motion.span layoutId="install-tab" className="absolute inset-0 rounded-2xl border border-line-2 bg-white/[0.04]" transition={{ type: "spring", stiffness: 100, damping: 20 }} />}
              <span className="relative flex items-center gap-3">
                <Icon size={18} weight="bold" className={on ? "text-signal" : "text-dim"} />
                <span className={`text-base font-medium ${on ? "text-fg" : "text-mute"}`}>{x.label}</span>
              </span>
              <span className={`relative mt-1.5 block pl-[30px] text-sm leading-relaxed ${on ? "text-mute" : "text-dim"}`}>{x.blurb}</span>
            </button>
          );
        })}
      </div>

      <div id="install-panel" role="tabpanel" className="overflow-hidden rounded-[1.75rem] border border-line bg-ink-2">
        <div className="flex items-center justify-between border-b border-line px-5 py-3">
          <div className="flex gap-1.5" aria-hidden>
            <span className="size-2.5 rounded-full bg-white/10" />
            <span className="size-2.5 rounded-full bg-white/10" />
            <span className="size-2.5 rounded-full bg-white/10" />
          </div>
          <button
            type="button"
            onClick={copy}
            className="flex cursor-pointer items-center gap-1.5 rounded-full px-3 py-1.5 font-mono text-xs text-mute transition hover:bg-white/5 hover:text-fg active:scale-[0.97]"
          >
            {copied ? <Check size={14} weight="bold" className="text-signal" /> : <Copy size={14} weight="bold" />}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
        <AnimatePresence mode="wait">
          <motion.pre
            key={t.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6, transition: { duration: 0.12 } }}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
            className="min-h-[220px] overflow-x-auto p-6 font-mono text-[13px] leading-7 text-fg/90 md:p-8"
          >
            {t.code.split("\n").map((line, i) => (
              <div key={i}>
                {line.startsWith("$ ") ? (
                  <>
                    <span className="select-none text-dim">$ </span>
                    {line.slice(2).split(/(\s+#.*)$/)[0]}
                    <span className="text-dim">{line.slice(2).split(/(\s+#.*)$/)[1]}</span>
                  </>
                ) : (
                  line || " "
                )}
              </div>
            ))}
          </motion.pre>
        </AnimatePresence>
      </div>
    </div>
  );
}
