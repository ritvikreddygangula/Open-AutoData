// Acceptance gate from Meta FAIR's AutoData (Agentic Self-Instruct).
export const GATE = {
  weakAvgMax: 65,
  weakMaxMax: 75,
  strongAvgMin: 60,
  strongAvgMax: 95,
  gapMin: 20,
  maxRounds: 3,
} as const;

export type Check = { id: string; label: string; detail: string; pass: boolean };

export const avg = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);

export function checkGate(weak: number[], strong: number[]) {
  const w = avg(weak);
  const s = avg(strong);
  const gap = s - w;
  const checks: Check[] = [
    { id: "wavg", label: "Weak avg ≤ 65", detail: w.toFixed(1), pass: w <= GATE.weakAvgMax },
    { id: "wmax", label: "Weak max ≤ 75", detail: String(Math.max(...weak)), pass: Math.max(...weak) <= GATE.weakMaxMax },
    { id: "wzero", label: "No zero scores", detail: weak.includes(0) ? "zero found" : "clean", pass: !weak.includes(0) },
    {
      id: "savg",
      label: "Strong avg in [60, 95)",
      detail: s.toFixed(1),
      pass: s >= GATE.strongAvgMin && s < GATE.strongAvgMax,
    },
    { id: "gap", label: "Gap ≥ 20", detail: gap.toFixed(1), pass: gap >= GATE.gapMin },
  ];
  return { checks, pass: checks.every((c) => c.pass), weakAvg: w, strongAvg: s, gap };
}
