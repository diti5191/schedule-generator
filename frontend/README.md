# Cardio Scheduler Frontend

This package delivers a dependency-light frontend for the CVA USA / The Heart House scheduling platform. It exposes framework-agnostic modules for managing vacation requests, visualising solver output, and tracking fairness metrics. All logic is implemented with native browser APIs so that the bundle can be embedded into a variety of stacks.

## Scripts

```bash
npm test        # execute the Node test runner over ./tests
npm start       # launch the zero-dependency static server on port 4173
```

## File Layout

- `src/main.js` – bootstraps the demo experience, hydrates sample data, and wires modules to DOM mount points.
- `src/store.js` – evented application store with allowance accounting helpers.
- `src/components/vacationForm.js` – vacation workflow renderer (draft → submitted → approved/denied) with allowance snapshots.
- `src/components/scheduleBoard.js` – transforms assignments + call rosters into a simple AM/PM table per weekday.
- `src/components/fairnessDashboard.js` – computes weekend call / hospital deltas against targets and renders summary tables.
- `src/utils/date.js` – timezone-safe helpers for ISO date arithmetic.
- `server.mjs` – static server that serves `public/` and ES modules from `src/` without extra dependencies.
- `tests/run-tests.mjs` – spawns Node's built-in `--test` runner. Unit tests live in `tests/*.test.mjs`.

## Testing Strategy

The tests stub DOM containers and exercise the modules as pure functions/classes, keeping the stack compatible with sandboxed CI systems that disallow third-party packages.

## Docker

A minimal `Dockerfile` is provided to run the test suite and serve static assets via the Node runtime. The container exposes port `4173`.

## Demo Data

The bootstrapper seeds a three-month (January–March 2026) window with representative providers, allowances, holidays, and schedule assignments so stakeholders can explore the UX without wiring the backend.