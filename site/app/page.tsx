import GateLab from "@/components/GateLab";
import { Hero, Nav } from "@/components/Hero";
import Install from "@/components/Install";
import PipelineSteps from "@/components/PipelineSteps";
import Results from "@/components/Results";
import { Footer, Marquee, Models, Problem, Research } from "@/components/Sections";
import { SectionHead } from "@/components/ui";

export default function Home() {
  return (
    <>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-fg focus:px-4 focus:py-2 focus:text-ink">
        Skip to content
      </a>
      <Nav />
      <main id="main">
        <Hero />
        <Marquee />
        <Problem />

        <section id="method" className="mx-auto max-w-[1400px] scroll-mt-16 px-4 py-24 md:px-8 md:py-28">
          <SectionHead n="02" kicker="The math gate" title={<>Five checks. <span className="text-mute">All must pass.</span></>}>
            Each solver answers three times and the judge scores every answer on its own. The weak model has to struggle without
            zeroing out, the strong model has to land without acing it, and the gap has to be at least 20 points. These are the exact
            thresholds from Meta&apos;s paper. Drag the runs and watch the gate decide.
          </SectionHead>
          <div className="mt-16 md:pl-[220px]">
            <GateLab />
          </div>
        </section>

        <section id="pipeline" className="mx-auto max-w-[1400px] scroll-mt-16 px-4 py-24 md:px-8 md:py-28">
          <SectionHead n="03" kicker="The pipeline" title={<>From a 10-Q <span className="text-mute">to a fine-tune file.</span></>}>
            A LangGraph state machine with one conditional edge that matters: revise or ship.
          </SectionHead>
          <div className="mt-16">
            <PipelineSteps />
          </div>
        </section>

        <Models />

        <section id="results" className="mx-auto max-w-[1400px] scroll-mt-16 px-4 py-24 md:px-8 md:py-28">
          <SectionHead n="05" kicker="The results" title={<>Measured, <span className="text-mute">not claimed.</span></>}>
            Meta&apos;s number sets the bar. Our blind benchmark, judged by a model that never touches the loop, shows whether we clear it.
          </SectionHead>
          <div className="mt-16 md:pl-[220px]">
            <Results />
          </div>
        </section>

        <section id="install" className="mx-auto max-w-[1400px] scroll-mt-16 px-4 py-24 md:px-8 md:py-28">
          <SectionHead n="06" kicker="Use it" title={<>Your documents. <span className="text-mute">Your key. Your dataset.</span></>}>
            Clone it, add an OpenRouter key, point it at any CSV of text chunks. SEC filings are the demo, not the limit.
          </SectionHead>
          <div className="mt-16 md:pl-[220px]">
            <Install />
          </div>
        </section>

        <Research />
      </main>
      <Footer />
    </>
  );
}
