# PokeFind MVP

PokeFind is a mobile-first marketplace for buying, selling, and negotiating
Pokémon trading cards in Thailand. It includes a React frontend and a Django
REST API, with Thai/English interfaces and THB/USD pricing.

## MVP features

- JWT registration and login for personal and business accounts
- Thai and English interface preferences
- THB and USD listing prices with configurable display conversion
- Listing discovery, search, filters, creation, editing, and deletion
- Saved-listing API
- Private buyer/seller conversations and messages
- Offers, seller acceptance or rejection, and two-party trade completion
- Django admin and deterministic demo data

Payments, escrow, delivery booking, live exchange rates, and production
real-time messaging are intentionally outside the MVP.

## Tech stack

- Frontend: React 19, TypeScript, Vite, Tailwind CSS, Vitest
- Backend: Python, Django 5.2, Django REST Framework, SimpleJWT
- Database: SQLite locally; PostgreSQL supported through environment variables

## Prerequisites

Install:

- Python 3.12 or newer
- Node.js 20.19+ or 22.12+
- pnpm 10 or newer (`corepack enable` can install pnpm)

The verified development environment used Python 3.12, Node.js 24, and pnpm
11.

## Quick start

Run these commands from the repository root.

### 1. Set up the backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py seed_demo
.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

Local development uses `backend/db.sqlite3`; no database server or backend
environment file is required.

Verify the API at [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/).
The expected response is:

```json
{"status": "ok"}
```

### 2. Set up the frontend

Open a second terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

The frontend already defaults to `http://localhost:8000/api`. To use another
API address:

```bash
cp .env.example .env
```

Then edit `VITE_API_URL` in `frontend/.env` and restart Vite.

## Demo accounts

Running `seed_demo` creates both accounts below. Their shared password is
`PokeFind123!`.

| Role | Email |
| --- | --- |
| Buyer | `buyer@pokefind.local` |
| Buyer 2 | `buyer2@pokefind.local` |
| Business seller | `seller@pokefind.local` |

The seed command is safe to run again and also creates sample listings, a
conversation, messages, and an offer.

## Tests and production build

From the repository root:

```bash
.venv/bin/python backend/manage.py test accounts.tests common.tests marketplace.tests messaging.tests
.venv/bin/python backend/manage.py check
cd frontend
pnpm test
pnpm build
```

The frontend production bundle is written to `frontend/dist/`.

## Configuration

### Frontend

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000/api` | Django API base URL |

Vite reads `frontend/.env` automatically when it starts.

### Backend

| Variable | Local default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Development-only key | Django signing secret |
| `DJANGO_DEBUG` | `1` | Enable Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Accepted host headers |
| `CORS_ALLOWED_ORIGINS` | Local Vite origins | Allowed frontend origins |
| `USD_TO_THB_RATE` | `35.00` | Fixed MVP display-conversion rate |
| `POSTGRES_DB` | Unset | Setting this enables PostgreSQL |
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |

Django reads these variables from the process environment; it does not load
`backend/.env.example` automatically. For example:

```bash
export DJANGO_SECRET_KEY='replace-with-a-long-random-secret'
export DJANGO_DEBUG=0
.venv/bin/python backend/manage.py runserver
```

## Optional PostgreSQL setup

Create a PostgreSQL database and export all `POSTGRES_*` variables before
running migrations:

```bash
export POSTGRES_DB=pokefind
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
.venv/bin/python backend/manage.py migrate
```

Unset `POSTGRES_DB` to return to the local SQLite database.

## Useful URLs

- Frontend: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- API health: [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/)
- Listings API: [http://127.0.0.1:8000/api/listings/](http://127.0.0.1:8000/api/listings/)
- Django admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

Create an admin account when needed:

```bash
.venv/bin/python backend/manage.py createsuperuser
```

## Project layout

```text
PokeFind_APP/
├── backend/
│   ├── accounts/       # Authentication and user preferences
│   ├── marketplace/    # Listings and saved cards
│   ├── messaging/      # Conversations, offers, and deals
│   └── config/         # Django settings and root URLs
├── frontend/
│   └── src/
│       ├── components/ # Shared UI components
│       ├── lib/        # API client and money utilities
│       └── pages/      # Application screens
└── docs/               # Product design and implementation plan
```

Shared API, money, localization, and deal-transition modules are used to keep
business rules and formatting DRY.

## Troubleshooting

### `Address already in use`

Another process is using port 8000 or 5173. Stop that process, or choose a
different port and update `VITE_API_URL` accordingly.

### The frontend reports a network or CORS error

Confirm the Django server is running, open the health URL, and ensure the exact
frontend origin appears in `CORS_ALLOWED_ORIGINS`. Restart both servers after
changing environment variables.

### Django reports missing tables

Run migrations and reseed the local database:

```bash
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py seed_demo
```

### The frontend starts with stale account preferences

Language, currency, and the JWT access token are stored in browser local
storage. Sign out or clear storage for `127.0.0.1:5173` to reset the browser
session.

## Production notes

Before deployment, use PostgreSQL, rotate the secret key, disable debug mode,
restrict allowed hosts and CORS, serve both applications over HTTPS, and move
uploaded media to durable object storage. Add production-grade email, payment,
delivery, monitoring, and WebSocket infrastructure only when those features
enter scope.
