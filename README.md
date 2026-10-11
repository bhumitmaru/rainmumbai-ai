# RainMumbai AI

Predictive modeling of the **RainMumbai Index** using meteorological data. A full-stack
web application (FastAPI + React) that ingests open-source weather forecasts, computes a
deterministic RainMumbai Index, produces a probabilistic prediction (current index,
predicted index, expected deviation, direction with probabilities, and a confidence
breakdown), and visualises it on a dashboard.

> **Disclaimer:** Predictions are probabilistic and based on historical data and current
> meteorological conditions. They do not guarantee future outcomes.

---

## Architecture

4-tier, modular design (frontend / API / pipeline / database), separated so each layer can
be maintained independently.

```
frontend (React + Vite + Tailwind + Recharts)
        │  HTTPS /api (JWT bearer)
        ▼
backend (FastAPI)
        ├── auth (JWT + bcrypt)
        ├── predictions / weather / performance / profitability / admin
        ├── pipeline: ingest → predict → evaluate
        └── APScheduler (hourly ingest+prediction, monthly evaluation)
        │
        ▼
database (SQLite for local dev; PostgreSQL supported via DATABASE_URL)
        └── D1 users · D3 meteo · D4 predictions/outcomes · D5 model metadata

external: Open-Meteo (ECMWF IFS/AIFS, NOAA GFS, DWD ICON + ensemble) — free, no API key
```

**No payments.** The product is free: there is no subscription table, no checkout/webhook,
and no payment gateway. Every authenticated user has full access (the PDF's `FR-12`/`UC-02`
subscription feature was removed per the product owner).

---

## RainMumbai Index definition (important assumption)

The PDF does not define the index formula. This implementation uses the **NCDEX RAINMUMBAI
Cumulative Deviation Rainfall (CDR)** recurrence, kept entirely in one swappable module
(`backend/app/index/service.py`) with weights/thresholds in `config/index.yaml`:

```
Rain_Mumbai(d)    = (Rain_Colaba(d) + Rain_Santacruz(d)) / 2
LPA_Mumbai(d)     = (LPA_Colaba(d) + LPA_Santacruz(d)) / 2
DailyDeviation(d) = Rain_Mumbai(d) - LPA_Mumbai(d)
Spot(d)           = Spot(d-1) + DailyDeviation(d)
On 1 June each year the Spot resets to the season LPA anchor (2206.7 mm), then that day's
deviation is added. Rainfall day d is the 24 hours ending 08:30 IST.
```

Because IMD daily LPA normals are not bundled, `backend/app/db/seed.py` generates a
deterministic **climatological daily LPA curve** (Gaussian seasonal profile scaled so the
monsoon season 1 Jun–30 Sep sums to 2206.7 mm) and labels it `source=climatology-seed`.
Replace this seed (or the whole formula) to use official values — see `config/index.yaml`.

From a forecast the system produces:

| Output | How |
|---|---|
| Current index | CDR spot at the latest completed IMD day |
| Predicted index (target timestamp) | current + forecast next-day deviation (optionally linear-calibrated) |
| Expected deviation | predicted − current |
| Direction | Increase / No Change / Decrease (threshold in config) |
| Direction probabilities | fraction of ensemble/multi-model members per direction (sum = 100%) |
| Category | Low / Moderate / High vs season anchor |

### Confidence breakdown

* **Data Quality** — completeness, freshness, and physical-range validity of inputs.
* **Model Performance** — rolling accuracy (MAE + direction accuracy) of past predictions vs observed outcomes.
* **Stability Score** — multi-model/ensemble spread plus run-to-run change.

Overall = weighted average (weights in `config/index.yaml`). Direction probabilities come
from ensemble members / multi-model spread, never invented numbers.

---

## Tech stack

* **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, JWT (python-jose),
  bcrypt, APScheduler, httpx.
* **Database:** SQLite (local dev); PostgreSQL supported via `DATABASE_URL`.
* **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Recharts, React Router, axios.
* **Testing:** Pytest (backend) + Vitest/Testing Library (frontend).

---

## Quick start

Backend (SQLite):

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env       # or set DATABASE_URL=sqlite:///./rainmumbai.db
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
pnpm install
pnpm dev                      # http://localhost:5173 (proxies /api to :8000)
```

* Frontend: http://localhost:5173
* Backend API / docs: http://localhost:8000/api/health , http://localhost:8000/docs

Default seeded admin: `admin@rainmumbai.ai` / `change-me-admin` (override via
`ADMIN_EMAIL` / `ADMIN_PASSWORD`). **Change these in production.**

---

## Environment variables (see `.env.example`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing secret (required in production) |
| `DATABASE_URL` | `sqlite:///...` or `postgresql+psycopg://...` |
| `CORS_ORIGINS` | comma-separated allowed origins |
| `MUMBAI_LAT/LON`, `COLABA_*`, `SANTACRUZ_*` | station coordinates |
| `OPEN_METEO_*_URL` | Open-Meteo forecast/ensemble/archive endpoints |
| `INDEX_CONFIG_PATH` | path to `config/index.yaml` |
| `SCHEDULER_ENABLED`, `HOURLY_INGEST_CRON`, `MONTHLY_EVAL_CRON` | background jobs |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | seeded admin account |
| `SMTP_ENABLED`, `FRONTEND_URL` | password-reset (mock email logs to backend) |

---

## API

All prediction/analytics endpoints require a `Authorization: Bearer <token>` header.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | create account |
| POST | `/api/auth/login` | login (JWT) |
| POST | `/api/auth/logout` | revoke token |
| POST | `/api/auth/forgot-password` | request reset (mock email) |
| POST | `/api/auth/reset-password` | reset password |
| GET | `/api/auth/me` | current profile |
| GET | `/api/predictions/latest` | cached current prediction |
| GET | `/api/predictions/history` | predicted vs actual history |
| GET | `/api/weather/current` | current conditions |
| GET | `/api/weather/forecast` | forecast + 24h rainfall |
| GET | `/api/performance` | MAE/RMSE/accuracy/F1 |
| GET | `/api/profitability` | rule-based historical P&L |
| GET | `/api/admin/overview` | ingestion status, jobs, counts (admin) |
| GET | `/api/admin/jobs` | job runs (admin) |
| GET | `/api/admin/users` | users (admin) |
| POST | `/api/admin/ingest` | trigger ingest+predict (admin) |
| POST | `/api/admin/evaluate` | trigger evaluation (admin) |
| GET | `/api/health` | liveness |

The current prediction is cached in the database (`is_current_cache`) and served without
recomputation, keeping the response well under the 5-second target.

---

## Requirements traceability

| FR | Feature | Where |
|---|---|---|
| FR-01 | Registration | `api/routes/auth.py` |
| FR-02 | Authentication | `api/routes/auth.py`, `core/security.py` |
| FR-03 | Data acquisition | `pipeline/ingest.py`, `providers/open_meteo.py` |
| FR-04 | Preprocessing | `pipeline/preprocess.py`, `pipeline/validate.py` |
| FR-05 | Index prediction | `index/service.py`, `pipeline/predict.py` |
| FR-06 | Confidence | `index/confidence.py` |
| FR-07 | Parameter visualisation | dashboard weather cards + charts |
| FR-08 | Historical tracking | `predictions`, `outcomes`, history page |
| FR-09 | Performance | `services/metrics.py`, `pipeline/evaluate.py` |
| FR-10 | Profitability | `services/profitability.py` |
| FR-11 | Dashboard | `pages/DashboardPage.tsx` |
| FR-12 | Subscription | **removed — free product** |
| FR-13 | Model updating | monthly **evaluation** (`pipeline/evaluate.py`), not retraining |
| FR-14 | Error handling | `core/exceptions.py`, request logging middleware |

### Monthly evaluation (replaces the PDF's monthly retraining)

`pipeline/evaluate.py` reconciles matured predictions, recomputes MAE/RMSE/direction-accuracy/F1,
stores a versioned `EvaluationRun`, and — only when the calibration layer is enabled — refits
the linear calibration and promotes it **only if it beats the active version**.

---

## Testing

```bash
# backend
cd backend && pytest

# frontend
cd frontend && pnpm test
```

---

## Project structure

```
backend/
  app/
    api/            # routers + auth deps
    core/           # config, security, logging, exceptions, datetime utils
    db/             # models (D1/D3/D4/D5), session, seed (LPA)
    index/          # NCDEX CDR formula + confidence
    jobs/           # APScheduler
    pipeline/       # ingest, predict, evaluate, state, preprocess, validate
    providers/      # WeatherProvider interface, Open-Meteo, cached fallback
    schemas/        # Pydantic request/response contract
    services/       # predictions, weather, performance, profitability, metrics, calibration, mailer
    main.py
  alembic/          # migrations
  tests/
config/index.yaml   # swappable index/confidence/profit configuration
frontend/
  src/
    api/ context/ components/ pages/ lib/
```
