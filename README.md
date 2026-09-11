# FinSight

A financial analytics, portfolio intelligence, and risk platform — cash flow and budget tracking, investment portfolio P/L, risk metrics (volatility, Sharpe ratio, drawdown), benchmark comparison, spending anomaly detection, rule-based insights, and a strategy backtester, built on a FastAPI + PostgreSQL backend and a React frontend.

> Student portfolio project. Built to demonstrate backend engineering, financial mathematics, and software design depth — not a production financial product. See [Security](#security) and [Known Limitations](#known-limitations--future-improvements) for what that means concretely.

## Problem

Personal finance tools tend to fall into two camps: simple budgeting apps that ignore investments entirely, or brokerage dashboards that ignore day-to-day cash flow. Neither gives someone a single place to see "am I saving enough, and is my portfolio actually taking on more risk than I realize" — and the ones that try rarely explain *how* a number like a Sharpe ratio was computed or what it assumes.

## Solution

FinSight combines a transaction/budget engine with a portfolio + risk engine on one data model, computed by an analytics layer that is deliberately transparent: every metric (savings rate, volatility, anomaly flags, insights) is a plain, documented formula over the user's own data — never an opaque model, never a fabricated number, and never a prediction dressed up as one.

## Features

- **Authentication** — registration, JWT-based login, per-resource authorization enforced at the service layer
- **Transactions** — CRUD with server-side filtering, sorting, and pagination (never loads a user's full history into memory)
- **CSV import** — validation → normalization → dedup → categorization → bulk insert, with a per-row error report
- **Cash flow & budget analytics** — income/expense/savings-rate, monthly trends, spending-by-category, budget-vs-actual, computed via SQL aggregation, not in Python
- **Portfolio engine** — trade ledger → derived holdings, cost basis, realized/unrealized P/L (weighted-average cost, `Decimal` throughout)
- **Market data** — pluggable provider (deterministic offline synthetic data by default; real `yfinance` data behind one config flag)
- **Risk engine** — volatility, Sharpe ratio, max drawdown, beta, correlation matrix, all NumPy, all unit tested against hand-computed values
- **Benchmark comparison** — portfolio vs. a benchmark (default SPY) over their honestly-overlapping date range
- **Anomaly detection** — Z-score and IQR, per-category, framed as "unusual" never "fraudulent"
- **Insight engine** — deterministic, rule-based sentences generated from real calculations, never an LLM guess
- **Backtesting** — moving-average crossover strategy, look-ahead-bias-free by construction (proven by a dedicated pair of unit tests, not just asserted in a comment)

## Architecture

```mermaid
flowchart TB
    subgraph Client
        FE["React + TypeScript frontend<br/>(Vite, Recharts)"]
    end

    subgraph Backend["FastAPI backend"]
        Routers["Routers<br/>(HTTP concerns only)"]
        Auth["Auth dependency<br/>(JWT verification)"]
        Services["Service layer<br/>(business rules, ownership checks)"]
        Analytics["Analytics engine<br/>(framework-free: cashflow, portfolio,<br/>risk, anomaly, insights, backtesting)"]
        Repos["Repository layer<br/>(SQLAlchemy queries)"]
    end

    DB[("PostgreSQL")]
    MD["Market data provider<br/>(local synthetic | yfinance)"]

    FE -->|HTTPS/JSON, Bearer JWT| Routers
    Routers --> Auth
    Auth --> Services
    Services --> Analytics
    Services --> Repos
    Repos --> DB
    Services --> MD
    MD -.cached prices.-> DB
```

The analytics engine (`backend/app/analytics/`) has **zero imports from FastAPI or SQLAlchemy** — every function is plain Python/NumPy/Decimal taking simple inputs and returning simple outputs. That's what makes it possible to unit test a Sharpe ratio or a backtest's look-ahead-bias behavior in milliseconds, with no database, no HTTP client, no fixtures.

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI | Async-capable, Pydantic-native validation, auto-generated OpenAPI docs for free |
| Validation | Pydantic v2 | Type-driven request/response schemas, decoupled from the ORM layer |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Explicit, typed models; versioned schema changes instead of hand-edited DDL |
| Database | PostgreSQL | Real constraint enforcement (FKs, uniqueness, CHECKs) rather than relying on application code alone; window functions and `date_trunc` used directly for analytics aggregation |
| Money | `Decimal` (`NUMERIC` columns) | Binary floating point cannot represent most decimal fractions exactly — unacceptable for ledger amounts a user is owed or owes |
| Stats/risk | NumPy | `float64` is the right tool for statistical *estimates* (noisy by nature), as opposed to ledger amounts |
| CSV | Pandas | Vectorized parsing/validation at the ingestion boundary only — never used to talk to the database (see [Engineering Challenges](#engineering-challenges)) |
| Auth | `python-jose` (JWT) + `bcrypt` | Stateless tokens; slow, salted password hashing |
| Frontend | React + Vite + TypeScript | Fast dev loop, typed API contracts, no framework magic to explain away in an interview |
| Charts | Recharts | Declarative, React-native, sufficient for this project's chart complexity |
| Infra | Docker Compose | One command to run backend + Postgres (+ frontend) together, identically on any machine |
| CI | GitHub Actions | Lint + full test suite (with a real Postgres service container) on every push |

## Database

Ten tables. `User`, `Account`, `Category` (user-scoped, seeded with defaults on registration), `Transaction`, `Budget`, `Asset` (shared reference data — not user-owned), `Portfolio`, `Trade`, `PriceHistory`, `Insight`.

Deliberately **not** modeled as separate tables: a `Benchmark` (it's just an `Asset` with `asset_class="benchmark"` — same price-history machinery), a `FinancialGoal` (no new engineering concept versus `Budget`), an `Alert` (would require a scheduler/notification system, out of scope). A `PortfolioHolding` table was also deliberately *not* built — current quantity, cost basis, and P/L are **derived** from the `Trade` ledger on every read (see `app/analytics/portfolio.py`), so there is no cached "current holding" row that can drift out of sync with what was actually bought and sold.

```mermaid
erDiagram
    User ||--o{ Account : owns
    User ||--o{ Category : owns
    User ||--o{ Transaction : owns
    User ||--o{ Budget : owns
    User ||--o{ Portfolio : owns
    User ||--o{ Insight : owns
    Account ||--o{ Transaction : contains
    Category ||--o{ Transaction : classifies
    Category ||--o{ Budget : limits
    Portfolio ||--o{ Trade : records
    Asset ||--o{ Trade : traded_in
    Asset ||--o{ PriceHistory : has

    User {
        uuid id PK
        string email UK
        string hashed_password
    }
    Transaction {
        uuid id PK
        uuid user_id FK
        uuid account_id FK
        uuid category_id FK
        numeric amount
        string transaction_type
        date date
        string import_hash
    }
    Trade {
        uuid id PK
        uuid portfolio_id FK
        uuid asset_id FK
        string trade_type
        numeric quantity
        numeric price
    }
```

Key integrity decisions enforced by Postgres, not just application code:
- Every user-owned table has `user_id` with `ON DELETE CASCADE` — deleting a user cleans up their data, no orphaned rows.
- `UNIQUE(account_id, import_hash)` on `Transaction` makes CSV re-import idempotent at the database level, not just in application logic.
- `UNIQUE(user_id, category_id)` on `Budget` — one budget per category, enforced structurally.
- Composite index `(user_id, date)` on `Transaction` for the filtered/paginated listing and analytics queries.
- Amounts are `NUMERIC`, never `FLOAT`.

## API

RESTful, versioned under `/api/v1`, documented live via OpenAPI at `/docs` once the backend is running. Every data-touching endpoint requires a Bearer JWT; ownership of the underlying resource is re-checked in the service layer on every read and write (a foreign key alone only proves an ID *exists*, not that it belongs to the caller).

Representative endpoints — the full, current list is authoritative at `/docs`:

```
POST   /api/v1/auth/register              POST   /api/v1/transactions/import
POST   /api/v1/auth/login                 GET    /api/v1/analytics/cashflow
GET    /api/v1/users/me                   GET    /api/v1/analytics/spending
GET    /api/v1/transactions               GET    /api/v1/analytics/budgets
POST   /api/v1/transactions               GET    /api/v1/analytics/anomalies
PUT    /api/v1/transactions/{id}          GET    /api/v1/portfolios/{id}/performance
DELETE /api/v1/transactions/{id}          GET    /api/v1/portfolios/{id}/risk
POST   /api/v1/portfolios/{id}/trades     GET    /api/v1/portfolios/{id}/benchmark
POST   /api/v1/backtests                  GET    /api/v1/insights
```

## Analytics

- **Savings rate** = `(income − expenses) / income`, explicitly `None` (not `0`) when income is zero — "0% savings rate" and "undefined, no income to save from" are different facts.
- **Budget status** — `under` / `approaching` (≥80% of limit) / `over` (≥100%).
- **Cost basis & P/L** — weighted-average cost method: every buy blends into one running average cost per share. Realized P/L locks in on sells against that average; unrealized P/L is `market_value − cost_basis` on open positions.
- **Volatility** — sample standard deviation of daily returns, annualized by `√252`.
- **Sharpe ratio** — mean excess return over its standard deviation, annualized; returns `None` (not an absurd number) when volatility is ~0, a real bug this project's own tests caught (see below).
- **Max drawdown** — worst peak-to-trough decline using the running maximum *seen so far* at each point (never a future peak).
- **Beta** — `cov(asset, benchmark) / var(benchmark)`.
- **Anomaly detection** — Z-score and IQR, run **per category** (comparing a $1,200 rent payment to a $15 coffee on one shared scale would flag rent every month).

None of these are predictions. They describe what already happened in the user's own data.

## Algorithms

- **Portfolio holdings from a trade ledger** — O(n) single pass over trades, weighted-average cost method, `Decimal` throughout. See `app/analytics/portfolio.py`.
- **CSV import** — O(n) vectorized validation via Pandas, O(1) dedup via a `UNIQUE(account_id, import_hash)` constraint and a single bulk `INSERT ... ON CONFLICT DO NOTHING` (not a per-row existence check).
- **Backtesting** — O(n) walk over a price series; the position decided from data through day *t* is applied with a strict one-period lag to the return realized from day *t* to day *t+1*, never to day *t*'s own return. This lag is the entire mechanism that prevents look-ahead bias, and it's covered by tests that construct a price jump and prove a signal decided *before* it captures the jump while a signal decided *after* it cannot retroactively capture a return that already happened.
- **Analytics aggregation** — pushed into Postgres (`GROUP BY`, `SUM`, `date_trunc`) rather than Python, so a user with a very large transaction history gets back a handful of aggregate rows, not every transaction pulled into memory.

## Testing

Two tiers, matched to what they test:

- **Unit tests** (`backend/tests/unit`) — the entire analytics engine (cashflow, portfolio, risk, anomaly, insights, backtesting) plus security primitives (hashing, JWT), all pure-Python/NumPy, no database, no HTTP. 71 tests, run in ~2.5 seconds.
- **Integration tests** (`backend/tests/integration`) — full API flows (register → login → authenticated request) against a real Postgres, with per-test table truncation for isolation.

**Run integration tests against a dedicated `*_test` database, never your dev database.** The session-level fixture drops every application table on teardown — correct for disposable test infrastructure, catastrophic against real data. `conftest.py` enforces this: it refuses to run (loud failure, not silent data loss) unless `DATABASE_URL`'s database name ends in `_test`. This isn't hypothetical — it's a mistake this project's own development hit once, wiping a local dev database mid-demo.

Deliberately tested: zero income (savings rate), zero volatility (Sharpe ratio), an empty portfolio, mismatched-length return series (beta/correlation), unauthenticated/invalid-token access, a nonexistent resource ID, look-ahead bias in the backtester (two dedicated tests), Z-score's known small-sample weakness (a documented limitation, proven with a test rather than just asserted).

## Security

- Passwords hashed with `bcrypt` (salted, deliberately slow) — never stored or logged in plaintext.
- JWTs signed (HS256), not encrypted — the payload carries only a user ID, nothing sensitive, because anyone holding the token can read it.
- `SECRET_KEY` has no default; the app refuses to start without one supplied via environment variable.
- Every data-touching endpoint requires authentication; ownership of the target resource is re-checked in the service layer, not assumed from a client-supplied ID.
- CSV import capped at 10MB to bound memory/CPU spent parsing an upload.
- CORS origins are explicit and configurable, not wildcarded.
- `pip-audit` runs in CI (non-blocking) — one known, currently-unfixed transitive vulnerability exists (`ecdsa`, pulled in by `python-jose`) but doesn't apply here, since JWTs are signed with HS256, never the ECDSA algorithms it affects.

**What this project does *not* have**, honestly: rate limiting on login/register (no brute-force protection beyond bcrypt's inherent slowness), token revocation/refresh flow (a stolen token is valid until its 30-minute expiry with no way to invalidate it early), email verification, or a password-reset flow. These are real gaps for a production system; they're absent here because they add infrastructure (a rate-limiter store, an email provider) beyond this project's scope, not because they were overlooked.

## Performance

- Transaction listing, filtering, sorting, and pagination happen entirely in SQL (`TransactionRepository.list_page`) — never "fetch everything, filter in Python."
- Cash flow/spending/budget aggregates are computed via `GROUP BY`/`SUM`/`date_trunc` in Postgres, not by pulling raw rows into Pandas.
- CSV import writes are a single bulk `INSERT ... ON CONFLICT DO NOTHING`, not N individual `session.add()` calls.
- Market data prices are cached into `PriceHistory` so repeated risk/backtest requests for the same asset/date range don't re-hit the (rate-limited, or simply slow) external provider.
- Composite index `(user_id, date)` on `Transaction` backs both the paginated listing and the date-range analytics queries.

## Running Locally

Requires Python 3.12+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then set a real SECRET_KEY
uvicorn app.main:app --reload
```

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/db   # requires Postgres running
```

A sample CSV (`docs/sample_transactions.csv`) is included for trying out `POST /api/v1/transactions/import` — register a user, create an account, then upload it via `/docs` or `curl`.

### Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/unit    # no database required
# Full suite (incl. integration tests) needs its own database — its
# teardown drops every table, so never point this at your dev database:
createdb finsight_test
DATABASE_URL=postgresql+psycopg://finsight:finsight@localhost:5432/finsight_test pytest
ruff check .
```

### Database migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend

Requires Node 22+.

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL defaults to http://localhost:8000
npm run dev
```

Then visit `http://localhost:5173`. `npm run build` type-checks and produces a production bundle in `dist/`; `npm run lint` runs oxlint (the Vite-scaffolded default).

## Docker

Requires Docker Desktop. Runs Postgres, the backend, and the frontend together.

```bash
cp backend/.env.example backend/.env   # then set a real SECRET_KEY
docker compose up --build
```

Frontend at `http://localhost:5173`, backend at `http://localhost:8000`. The frontend's API URL is baked into its static bundle at Docker build time (`VITE_API_URL` build arg in `docker-compose.yml`) — a Vite limitation, not a compose oversight: env vars aren't readable inside a static bundle at container *runtime*, only at build time.

## Deploying to Production

**Important constraint to understand first:** Vercel runs serverless functions and static frontends — it cannot host the FastAPI backend as built here (a long-lived process with a pooled database connection and Alembic migrations). The split that works: **Vercel for the frontend only**, a container host for the backend, and a managed Postgres. This project uses **Render** (backend, runs the existing `Dockerfile` directly, free tier available) and **Neon** (serverless Postgres, free tier, no local install needed) — but any Docker-capable host + any Postgres provider works the same way.

### 1. Database (Neon)

1. Create a free project at neon.tech.
2. Copy its connection string (starts `postgresql://...`) and rewrite the scheme to `postgresql+psycopg://...` (this project's `DATABASE_URL` uses the `psycopg` v3 driver explicitly — see `app/database.py`).

### 2. Backend (Render)

This repo includes `render.yaml` at the root, so Render can deploy it as a Blueprint:

1. In Render, **New → Blueprint**, point it at this repo.
2. It reads `render.yaml` and creates a `finsight-backend` web service from `backend/Dockerfile`.
3. Before the first deploy, set these in the Render dashboard (the blueprint marks them `sync: false` deliberately — they're secrets, never committed):
   - `DATABASE_URL` — the Neon connection string from step 1
   - `CORS_ORIGINS` — a JSON array containing your Vercel URL once you have it, e.g. `["https://finsight.vercel.app"]` (you'll come back and set this after step 3)
4. `SECRET_KEY` is auto-generated by Render; leave it alone.
5. Render runs `alembic upgrade head` automatically before every start (see `render.yaml`'s `startCommand`) — migrations are never a manual step.
6. Once deployed, confirm `https://<your-service>.onrender.com/health` and `/health/db` both return `200`.

### 3. Frontend (Vercel)

1. In Vercel, **Add New → Project**, import this repo.
2. Set **Root Directory** to `frontend` (this is a monorepo — Vercel needs to be told the frontend doesn't live at the repo root).
3. Framework preset: Vite (Vercel should auto-detect it from `frontend/package.json`). `frontend/vercel.json` already handles the SPA rewrite React Router needs (without it, refreshing on e.g. `/dashboard` would 404).
4. Set the environment variable `VITE_API_URL` to your Render backend URL from step 2 (e.g. `https://finsight-backend.onrender.com`) — this gets compiled into the build, same build-time-not-runtime caveat as the Docker build arg above.
5. Deploy. Take the resulting `https://*.vercel.app` URL back to step 2 and set it as `CORS_ORIGINS` on Render (then redeploy the backend so the new CORS origin takes effect).

### Order matters

Deploy the database first, the backend second (it needs the database URL), and the frontend last (it needs the backend URL) — then loop back once to put the frontend's final URL into the backend's CORS config. This two-way dependency (backend needs frontend's URL for CORS; frontend needs backend's URL to call it) is unavoidable with this split and is why the loop-back step exists rather than being a bug in the instructions above.

## Engineering Challenges

- **A dependency compatibility break, diagnosed and simplified past rather than pinned around.** `passlib`'s `CryptContext` (the standard tutorial pattern for bcrypt in FastAPI) broke immediately with `AttributeError: module 'bcrypt' has no attribute '__about__'` — passlib is unmaintained since 2020 and its internal self-test pokes at an attribute newer `bcrypt` releases removed. Rather than pin `bcrypt<4.1` (deferring the problem, leaving a stale dependency), the fix was to drop passlib entirely and call `bcrypt.hashpw`/`bcrypt.checkpw` directly — fewer moving parts, same security properties.
- **A real bug, caught by its own test suite.** `sharpe_ratio`'s zero-volatility guard used `std == 0`. Floating-point returns computed from prices essentially never hit *exactly* zero (a constant 10%-per-period series still has ~1e-17 of float error in its std), so the guard silently failed and produced a meaningless ~1e16 ratio instead of the correctly-undefined `None`. Fixed with an explicit `np.isclose` tolerance; the failing test is what surfaced it.
- **A flaky test, and why it was flaky.** A JWT-tampering test flipped the *last* character of a token and expected verification to fail — but base64url's final symbol only encodes a partial byte (the unused trailing bits are padding that decoding ignores), so roughly 1 in 4 replacement characters decoded to the *same* bytes, and the "tampered" token verified anyway about a quarter of the time. Fixed by tampering a character in the middle of the token instead, which always changes a full byte.
- **Look-ahead bias in the backtester, proven, not just avoided.** It's easy to *write* a backtester that doesn't look ahead and much harder to *prove* it doesn't. The engine applies a strategy's day-*t* signal to the day-*t*-to-*t+1* return with a strict lag; two tests construct a price series with a single sharp jump and check that a signal decided before the jump captures it while a signal decided after cannot retroactively capture a return that already happened — the exact property a subtly-broken implementation would get backwards.
- **Market data without a paid API or flaky test runs.** Real market data (`yfinance`) is free but unofficial, rate-limited, and often unreachable from CI runners or sandboxed dev environments — exactly where this project most needs reliability. The market data layer is a `Protocol` with two implementations: a deterministic, seeded synthetic-price generator (same symbol + date range → same prices, every run, everywhere, no network) used by default, and a real `yfinance` provider swapped in via one config value for production use.
- **Deriving state instead of storing it.** Portfolio holdings could have been a mutable `PortfolioHolding` row updated on every trade — simpler to query, but able to drift from the trade history that's supposed to be its source of truth. Holdings are instead recomputed from the full `Trade` ledger on every read. More computation per request; structurally impossible to have a holding disagree with the trades that produced it.
- **A database constraint gap the DDL made visible only when compared against itself.** SQLAlchemy's `Enum(native_enum=False)` looks like it should add a `CHECK` constraint restricting a column to valid enum values — it doesn't, by default (`create_constraint` defaults to `False`). All four enum-valued columns (`transaction_type`, `trade_type`, `account_type`, `asset_class`) were validated only by Pydantic at the API boundary, with nothing stopping an invalid value via any other path. Caught by literally compiling each table's DDL and reading it, not by inspection — the fix (`create_constraint=True` plus matching hand-written `CHECK` clauses in the migration) surfaced a second, related issue: SQLAlchemy's default enum persistence stores the Python member's *name* (`"EXPENSE"`), not its *value* (`"expense"`) — inconsistent with the lowercase strings the API actually sends. Fixed with `values_callable`.
- **A static frontend can't read runtime environment variables — only build-time ones.** `VITE_API_URL` looks like an ordinary env var, but Vite inlines it into the JavaScript bundle at `npm run build` time; setting it as a container `environment:` entry (rather than a Docker build `arg`) would silently do nothing, since by the time the container runs, the bundle is already frozen. Both `docker-compose.yml` and the Vercel deployment steps pass it at build time specifically because of this.
- **A local dev database, wiped by its own test suite, mid-demo.** The integration test fixture's teardown drops every table in `Base.metadata` — correct for disposable test infrastructure. Running the full suite with `DATABASE_URL` pointed at the local dev database (instead of a dedicated test database) triggered exactly that teardown against real, just-created data. Worse: Alembic's own version-tracking table isn't part of the app's metadata, so it survived the wipe — meaning Alembic believed the schema was already current and refused to recreate anything on a plain `upgrade head`, until its tracking row was cleared by hand to force a full re-run. Fixed two ways: recovered the immediate data loss, and added a guard to the fixture itself that refuses to run (loud failure) against any database not named `*_test` — turning "pointed at the wrong database" from a silent, unrecoverable mistake into an error you see before it happens again.

## Known Limitations & Future Improvements

- No rate limiting on authentication endpoints.
- No token revocation/refresh flow.
- Portfolio risk metrics apply *today's* position sizes across the entire lookback window rather than replaying actual historical position sizes on each date — stated explicitly in the API response's `warning` field when relevant, not hidden.
- Backtest runs are not persisted (`GET /backtests/{id}` from the original API sketch was deliberately not built — it implies a new table and run-history semantics that didn't fit this pass; `POST /backtests` returns the full result synchronously instead).
- Only one backtesting strategy (moving-average crossover) is implemented, chosen deliberately over three shallow ones; the `Strategy` shape is structured to make adding momentum/mean-reversion straightforward.
- Monte Carlo simulation was scoped as optional/stretch in the original plan and not built in this pass.
- No email verification or password reset flow.
- The frontend stores its JWT in `localStorage`, which is readable by any script on the page — vulnerable to XSS-based token theft. A production system would use an httpOnly cookie with a refresh-token flow instead; documented inline in `frontend/src/api/client.ts` and on the Settings page, not hidden.
- No dedicated UI for spending anomaly detection (`GET /analytics/anomalies` is implemented and tested on the backend, but wasn't in the frontend page list this pass).
- Frontend visual rendering (actual chart output, responsive layout) was verified via successful build + a curled dev-server response, not by visual/screenshot inspection — an honest gap in this environment rather than a claimed-and-skipped step.

---

*Built with substantial AI assistance (Claude), used deliberately as a teaching tool rather than a black box — every non-trivial design decision above was explained and understood before being committed, not merely accepted.*
