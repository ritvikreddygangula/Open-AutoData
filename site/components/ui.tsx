import type { ReactNode } from "react";

export function Logo({ name, className = "size-5", color = false }: { name: string; className?: string; color?: boolean }) {
  const mask = { maskImage: `url(/logos/${name}.svg)`, WebkitMaskImage: `url(/logos/${name}.svg)` };
  return (
    <span aria-hidden className={`relative inline-block shrink-0 ${className}`}>
      <span className={`logo-mask absolute inset-0 transition-opacity duration-300 ${color ? "group-hover:opacity-0" : ""}`} style={mask} />
      {color && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`/logos/${name}-color.svg`}
          alt=""
          className="absolute inset-0 size-full opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        />
      )}
    </span>
  );
}

// The gate mark: two posts and the one question that makes it through.
export function Mark({ className = "size-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden>
      <rect x="3" y="4" width="3" height="16" rx="1.5" fill="currentColor" />
      <rect x="18" y="4" width="3" height="16" rx="1.5" fill="currentColor" />
      <circle cx="12" cy="12" r="2.6" fill="var(--color-signal)" />
    </svg>
  );
}

export function SectionHead({ n, kicker, title, children }: { n: string; kicker: string; title: ReactNode; children?: ReactNode }) {
  return (
    <div className="grid gap-6 md:grid-cols-[180px_1fr] md:gap-10">
      <div className="flex items-baseline gap-3 font-mono text-xs uppercase tracking-[0.18em] text-dim md:flex-col md:gap-2">
        <span className="text-signal">{n}</span>
        <span>{kicker}</span>
      </div>
      <div className="max-w-3xl">
        <h2 className="text-3xl font-medium leading-[1.05] tracking-tighter text-fg md:text-5xl">{title}</h2>
        {children && <p className="mt-5 max-w-[62ch] text-base leading-relaxed text-mute md:text-lg">{children}</p>}
      </div>
    </div>
  );
}

const STATUS_STYLE: Record<string, string> = {
  ACCEPTED: "text-signal bg-signal/10 ring-signal/30",
  REVISE: "text-warn bg-warn/10 ring-warn/30",
  REJECTED: "text-fail bg-fail/10 ring-fail/30",
  ERROR: "text-fail bg-fail/10 ring-fail/30",
  PENDING: "text-mute bg-white/5 ring-white/10",
};

export function StatusPill({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[11px] tracking-wider ring-1 ring-inset ${STATUS_STYLE[status] ?? STATUS_STYLE.PENDING}`}>
      <span className="size-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}

export function DemoBadge() {
  return (
    <span
      title="Sample records built from real SEC chunks. Replaced automatically when the pipeline writes data/trajectories.json."
      className="rounded-full border border-dashed border-warn/40 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-warn"
    >
      Demo data
    </span>
  );
}

/** Weak and strong averages on one 0 to 100 track, with the paper's thresholds marked. Transform-only motion. */
export function GapMeter({ weak, strong, pass }: { weak: number; strong: number; pass: boolean }) {
  const lo = Math.min(weak, strong);
  const span = Math.abs(strong - weak);
  const ease = "transform 700ms cubic-bezier(0.16, 1, 0.3, 1)";
  return (
    <div className="relative h-10 select-none" aria-label={`Weak ${weak.toFixed(1)}, strong ${strong.toFixed(1)}`}>
      <div className="absolute inset-x-0 top-4 h-1.5 rounded-full bg-white/[0.06]" />
      {/* acceptable zones */}
      <div className="absolute top-4 left-0 h-1.5 w-[65%] rounded-l-full bg-white/[0.05]" />
      <div className="absolute top-4 left-[60%] h-1.5 w-[35%] bg-signal/10" />
      <div
        className={`absolute inset-x-0 top-4 h-1.5 origin-left rounded-full ${pass ? "bg-signal" : strong < weak ? "bg-fail" : "bg-warn"}`}
        style={{ transform: `translateX(${lo}%) scaleX(${span / 100})`, transition: ease }}
      />
      {[60, 65, 95].map((t) => (
        <div key={t} className="absolute top-3 h-3.5 w-px bg-white/25" style={{ left: `${t}%` }}>
          <span className="absolute top-5 -translate-x-1/2 font-mono text-[9px] text-dim">{t}</span>
        </div>
      ))}
      {[
        { v: weak, label: "W", cls: "bg-fg text-ink" },
        { v: strong, label: "S", cls: "bg-signal text-signal-ink" },
      ].map((m) => (
        <div key={m.label} className="absolute inset-0" style={{ transform: `translateX(${m.v}%)`, transition: ease }}>
          <span className={`absolute top-[9px] grid size-5 -translate-x-1/2 place-items-center rounded-full font-mono text-[10px] font-semibold ${m.cls}`}>
            {m.label}
          </span>
        </div>
      ))}
    </div>
  );
}
