# OpenAutodata website

The project site and live run log. See the [main README](../README.md) for the pipeline.

```bash
npm install
npm run dev     # http://localhost:3000
npm run build   # static export to out/
```

`npm run dev` and `npm run build` first copy `../data/trajectories.json` and `../data/benchmark.json` into `public/data/` when they exist. Until the pipeline has run, the site shows a demo set built from real SEC chunks, marked with a "Demo data" badge.
