"use client";

import { useEffect, useState } from "react";
import { avg } from "./gate";

export type Status = "ACCEPTED" | "REVISE" | "REJECTED" | "PENDING";

// One record per round, written by src/state.py:to_record().
export type RawRecord = {
  run_id?: string;
  arm?: "loop" | "baseline";
  chunk_id: string | number;
  round_num: number;
  question_type?: string;
  skill_tags?: string[];
  context?: string;
  question?: string;
  reference_answer?: string;
  rubric?: { criterion: string; weight: number }[];
  weak_attempt_scores?: number[];
  strong_attempt_scores?: number[]; // empty when the weak gate failed and strong never ran
  weak_score?: number | null;
  strong_score?: number | null;
  score_gap?: number | null;
  judge_feedback?: string | null;
  verifier_feedback?: string | null;
  failure_mode?: "TOO_EASY" | "TOO_HARD" | "FAILED_ON_STRONG" | "FAILED_QV" | null;
  fail_reason?: string | null;
  status: Status;
  source?: string; // site-only label for demo records
  demo?: boolean;
};

export type Traj = RawRecord & {
  weak: number[];
  strong: number[];
  weakAvg: number;
  strongAvg: number;
  strongRan: boolean;
  gap: number | null;
};

export function normalize(r: RawRecord): Traj {
  const weak = r.weak_attempt_scores ?? [];
  const strong = r.strong_attempt_scores ?? [];
  const weakAvg = r.weak_score ?? avg(weak);
  const strongAvg = r.strong_score ?? avg(strong);
  const strongRan = strong.length > 0;
  return { ...r, weak, strong, weakAvg, strongAvg, strongRan, gap: r.score_gap ?? (strongRan && weak.length ? strongAvg - weakAvg : null) };
}

export const FAILURE_LABEL: Record<string, string> = {
  TOO_EASY: "Too easy",
  TOO_HARD: "Too hard",
  FAILED_ON_STRONG: "Failed on strong",
  FAILED_QV: "Failed quality check",
};

export type Benchmark = {
  baseline_gap: number;
  openautodata_gap: number;
  baseline_weak: number;
  openautodata_weak: number;
  baseline_strong: number;
  openautodata_strong: number;
  judge_preference_pct?: number;
  n?: number;
};

type Load<T> = { state: "loading" } | { state: "error"; message: string } | { state: "ready"; data: T };

export function useJson<T>(path: string, poll = 0): Load<T> {
  const [res, setRes] = useState<Load<T>>({ state: "loading" });
  useEffect(() => {
    let alive = true;
    const load = () =>
      fetch(path, { cache: "no-store" })
        .then((r) => {
          if (!r.ok) throw new Error(r.status === 404 ? "not found" : `HTTP ${r.status}`);
          return r.json() as Promise<T>;
        })
        .then((data) => alive && setRes({ state: "ready", data }))
        .catch((e: Error) => alive && setRes((prev) => (prev.state === "ready" ? prev : { state: "error", message: e.message })));
    load();
    const id = poll ? setInterval(load, poll) : undefined;
    return () => {
      alive = false;
      if (id) clearInterval(id);
    };
  }, [path, poll]);
  return res;
}
