// Copies pipeline output (../data) into public/data so the site shows real runs instead of the demo set.
import { copyFileSync, existsSync } from "node:fs";

for (const f of ["trajectories.json", "benchmark.json"]) {
  const src = new URL(`../data/${f}`, import.meta.url);
  if (existsSync(src)) {
    copyFileSync(src, new URL(`./public/data/${f}`, import.meta.url));
    console.log(`synced ${f}`);
  }
}
