# PokeFind MVP

PokeFind is a mobile-first marketplace for buying, selling, and negotiating
Pokémon trading cards in Thailand. It includes a React frontend and a Django
REST API, with Thai/English interfaces and THB/USD pricing.

## MVP features

- JWT registration and login for personal and business accounts
- Password reset by email (single-use links that expire after an hour)
- Thai and English interface preferences
- THB and USD listing prices with configurable display conversion
- Listing discovery, search, filters, creation, editing, and deletion
- Saved-listing API
- Private buyer/seller conversations and messages
- Offers and counter-offers answered by the other party; accepting reserves the
  listing. Sellers can also reserve a card for a buyer directly from chat (no
  buyer acceptance). Either side can cancel before confirming, and both confirm
  completion
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
cp backend/.env.example backend/.env
```

Edit `backend/.env`: set `DJANGO_SECRET_KEY` (generate one with
`python3 -c "import secrets; print(secrets.token_urlsafe(50))"`),
`DJANGO_PASSWORD_PEPPER` (generated the same way) and `DEMO_SEED_PASSWORD`
(the password the demo accounts will get). Then:

```bash
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py seed_demo
.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

Django loads `backend/.env` automatically; real environment variables take
precedence. Local development (`DJANGO_DEBUG=1`) uses `backend/db.sqlite3`.

Password-reset emails are printed in the runserver console during local development.

Verify the API at [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/).
The expected response is:

```json
{"status": "ok"}
```

### 2. Set up the frontend

Open a second terminal:

```bash
cd frontend
cp .env.example .env.development.local
pnpm install
pnpm dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

`VITE_API_URL` is required; there is no built-in default. Every build
(Figma Make `deploy` and `deploy-preview`) refuses to run without it or with a
`localhost` URL, so set the real API URL in the build environment.

## Demo accounts

`seed_demo` (development only, `DJANGO_DEBUG=1`) creates the accounts below.
They all use the password in `DEMO_SEED_PASSWORD`. To make the hidden demo
picker on the sign-in page fill it in, set `DEMO_PASSWORD` to the same value in
`frontend/.env.development.local`. Only the local dev server sees it; it is
never put into a build.

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
VITE_API_URL=https://api.example.com/api pnpm build
```

Builds fail on purpose when `VITE_API_URL` is missing or points at localhost. CI that
runs backend tests on PostgreSQL with `DJANGO_DEBUG=0` must also set
`DJANGO_SECURE_SSL_REDIRECT=0`.

The frontend production bundle is written to `frontend/dist/`.

## Configuration

Nothing secret or environment-specific is hard-coded. Startup fails with a
message naming any missing required variable.

### Frontend

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | yes | Django API base URL, including `/api` |
| `DEMO_PASSWORD` | no | Local dev server only: fills the demo-account picker (never bundled) |

### Backend

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DJANGO_SECRET_KEY` | yes | — | Signs sessions and JWTs |
| `DJANGO_PASSWORD_PEPPER` | yes | — | Secret mixed into every password hash (≥ 32 random chars, e.g. `secrets.token_urlsafe(48)`). Never change or lose it: every user would have to reset |
| `DJANGO_DEBUG` | no | `0` | `1` for local development only |
| `DJANGO_ALLOWED_HOSTS` | yes | — | Accepted host headers |
| `CORS_ALLOWED_ORIGINS` | yes | — | Allowed frontend origins |
| `FRONTEND_URL` | yes | — | Public web-app URL used in reset emails (`https://` in production) |
| `EMAIL_HOST`, `DEFAULT_FROM_EMAIL` | in production | — | SMTP server and sender for reset emails |
| `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | no | `587` / — / — | SMTP connection |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | no | `1` / `0` | SMTP encryption |
| `PASSWORD_RESET_TIMEOUT_MINUTES` | no | `60` | How long a reset link works |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` | in production | — | PostgreSQL connection (required when `DJANGO_DEBUG` is not `1`) |
| `POSTGRES_PORT` | no | `5432` | PostgreSQL port |
| `DJANGO_BEHIND_TLS_PROXY` | no | `0` | `1` when a proxy terminates TLS and sets `X-Forwarded-Proto` |
| `DJANGO_SECURE_SSL_REDIRECT` | no | `1` | Redirect HTTP to HTTPS (production) |
| `DJANGO_SECURE_HSTS_SECONDS` | no | `31536000` | HSTS max-age (production) |
| `DJANGO_NUM_PROXIES` | no | `0` | Proxies appending to `X-Forwarded-For`; must match your infrastructure or rate limits break |
| `REDIS_URL` | no | — | Shared cache for rate limits across workers |
| `THROTTLE_ANON_RATE` / `THROTTLE_USER_RATE` / `THROTTLE_AUTH_RATE` / `THROTTLE_PASSWORD_RESET_RATE` | no | `120/min` / `600/min` / `10/min` / `10/hour` | Rate limits (`auth` = login, register and setting a new password; `password_reset` = reset-email requests) |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | no | `15` / `7` | Token lifetimes |
| `MAX_UPLOAD_MB` | no | `5` | Largest avatar/photo upload |
| `USD_TO_THB_RATE` | no | `35.00` | Fixed MVP display-conversion rate |
| `DEMO_SEED_PASSWORD` | for `seed_demo` | — | Password for demo accounts (dev only) |

See `backend/.env.example` for a ready-to-copy file.

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

Language, currency, and the JWT access and refresh tokens are stored in browser local
storage. Sign out or clear storage for `127.0.0.1:5173` to reset the browser
session.

## Production notes

Run with `DJANGO_DEBUG` unset, PostgreSQL, a fresh `DJANGO_SECRET_KEY`, and
exact `DJANGO_ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`. Set `DJANGO_NUM_PROXIES`
and `DJANGO_BEHIND_TLS_PROXY` to match your load balancer, use `REDIS_URL`
when running several workers, and cap request bodies in the proxy (for
example nginx `client_max_body_size 6m`). `manage.py check --deploy` should
report no issues. Run `manage.py flushexpiredtokens` daily to prune the JWT
blacklist. Uploaded media still needs durable object storage before photos
can be served.

Store `DJANGO_PASSWORD_PEPPER` in a secret manager and back it up separately from
the database. Passwords are Argon2id with a per-user salt and this pepper; older
PBKDF2 hashes are upgraded when each user next signs in.

Tokens carry a fingerprint of the password hash, so a password change or reset
ends every session at once. Deploying this release therefore signs every user
out once, and the PBKDF2 upgrade signs out that user's other devices once.

Keep `/admin/` off the public internet (proxy IP allowlist or VPN). Its login
is rate-limited like the API login, but it guards the most powerful accounts.
