# FinSight frontend

React + TypeScript + Vite client for the FinSight backend (FastAPI).

## Development

```bash
npm install
cp .env.example .env   # set VITE_API_URL if not using the default
npm run dev
```

The dev server runs on `http://localhost:5173` and expects the backend at
`VITE_API_URL` (defaults to `http://localhost:8000`).

## Scripts

- `npm run dev` — start the Vite dev server
- `npm run build` — type-check (`tsc -b`) and produce a production build in `dist/`
- `npm run lint` — run oxlint
- `npm run preview` — preview the production build locally

## Docker

```bash
docker build --build-arg VITE_API_URL=http://localhost:8000 -t finsight-frontend .
docker run -p 5173:80 finsight-frontend
```

`VITE_API_URL` is compiled into the static bundle at build time (Vite env
vars aren't readable at container runtime), so it must be passed as a build
arg, not a runtime environment variable. The container serves the built
assets via nginx on port 80.

## Known limitations

- The auth JWT is stored in `localStorage`. That's acceptable for this
  project's scope but is vulnerable to token theft via XSS; a production
  deployment would use an httpOnly cookie instead.
- No automated tests are included.
