"use client";

import { useRef } from "react";
import { motion, useScroll, useSpring } from "motion/react";
import { ArrowUpRight } from "@phosphor-icons/react";
import { Logo, Mark } from "./ui";

const STEPS = [
  {
    t: "Ingest",
    logos: ["snowflake"],
    d: "SQL pulls the Results of Operations section of real 10-Q filings from Snowflake Marketplace, cleans them and splits them into chunks.",
    io: "SELECT filing text → data/chunks.json",
  },
  {
    t: "Challenge",
    logos: ["zhipu"],
    d: "GLM-5.3 reads one chunk and writes four things: a context with only the facts needed, a multi-step question, a reference answer, and a 10 to 15 criterion rubric with weights from 1 to 7.",
    io: "chunk → { context, question, reference_answer, rubric }",
  },
  {
    t: "Quality check",
    logos: ["nvidia"],
    d: "Before any solving, Nemotron 3 Super checks that the context does not leak the answer, the question tests reasoning rather than recall, and every calculation criterion states its expected value.",
    io: "package → PASS | FAIL",
  },
  {
    t: "Solve",
    logos: ["meta", "deepseek"],
    d: "Llama 3.2 3B answers three times from the context alone, never the filing or the reference answer. DeepSeek V4.1 Flash gets the identical prompt three times, every round, so each round has a gap.",
    io: "context + question → 3 weak, then 3 strong answers",
  },
  {
    t: "Judge",
    logos: ["nvidia"],
    d: "Nemotron 3 Super grades each answer on its own: met or not met, criterion by criterion. It never sees the reference answer. Code turns the verdicts into a weighted 0 to 100 score.",
    io: "each answer → met / not met per criterion → score",
  },
  {
    t: "Gate",
    logos: [],
    d: "node_evaluate runs the paper's checks. A failure is labelled too easy, too hard, failed on strong or failed quality check, and the Challenger writes an entirely new question with the judge's notes. Three rounds, then the chunk is discarded with its reason logged.",
    io: "scores → ACCEPTED | REVISE | REJECTED",
  },
  {
    t: "Persist",
    logos: ["snowflake", "huggingface"],
    d: "Every round lands in OPENAUTODATA_TRAJECTORIES. Accepted pairs land in OPENAUTODATA_ACCEPTED_SET, ready to export for fine-tuning.",
    io: "→ Snowflake + data/accepted.json",
  },
];

export default function PipelineSteps() {
  const ref = useRef<HTMLOListElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 70%", "end 60%"] });
  const scaleY = useSpring(scrollYProgress, { stiffness: 100, damping: 20 });

  return (
    <div className="grid gap-12 md:grid-cols-[180px_1fr] md:gap-10">
      <div className="hidden md:block">
        <div className="sticky top-24 space-y-4">
          <div className="flex items-center gap-2 text-mute">
            <Logo name="langgraph" className="size-5 text-fg" />
            <span className="text-sm">LangGraph StateGraph</span>
          </div>
          <a href="/Data_flow.png" className="inline-flex items-center gap-1.5 text-sm text-mute underline decoration-line-2 underline-offset-4 transition hover:text-fg">
            Full data-flow diagram <ArrowUpRight size={13} weight="bold" />
          </a>
        </div>
      </div>

      <ol ref={ref} className="relative">
        <div className="absolute top-2 bottom-2 left-[19px] w-px bg-line" aria-hidden />
        <motion.div className="absolute top-2 bottom-2 left-[19px] w-px origin-top bg-signal" style={{ scaleY }} aria-hidden />
        {STEPS.map((s, i) => (
          <motion.li
            key={s.t}
            initial={{ opacity: 0, x: 24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
            className="relative grid grid-cols-[40px_1fr] gap-x-6 pb-14 last:pb-0"
          >
            <span className="relative z-10 grid size-10 place-items-center rounded-full border border-line-2 bg-ink font-mono text-xs text-fg">
              {String(i + 1).padStart(2, "0")}
            </span>
            <div className="grid gap-4 md:grid-cols-[1fr_auto] md:gap-10">
              <div>
                <h3 className="text-2xl font-medium tracking-tight text-fg md:text-3xl">{s.t}</h3>
                <p className="mt-3 max-w-[58ch] text-[15px] leading-relaxed text-mute md:text-base">{s.d}</p>
                <code className="mt-4 inline-block rounded-lg border border-line bg-ink-2 px-3 py-1.5 font-mono text-xs text-mute">{s.io}</code>
              </div>
              <div className="flex gap-2 md:pt-1">
                {s.logos.length ? (
                  s.logos.map((l) => (
                    <span key={l} className="group grid size-12 place-items-center rounded-2xl border border-line bg-ink-2 text-fg">
                      <Logo name={l} color className="size-6" />
                    </span>
                  ))
                ) : (
                  <span className="grid size-12 place-items-center rounded-2xl border border-signal/30 bg-signal/10 text-fg">
                    <Mark className="size-6" />
                  </span>
                )}
              </div>
            </div>
          </motion.li>
        ))}
      </ol>
    </div>
  );
}
