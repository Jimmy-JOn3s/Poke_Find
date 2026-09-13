# PokeFind MVP

Mobile-first Pokemon TCG marketplace for Thailand. The frontend is based on the approved Figma Make export; the backend is a Django REST API. Thai/English interface preferences and THB/USD listing/display currencies are supported.

## Included

- JWT registration/login and personal/business profiles
- Thai and English interface switching
- THB and USD listing prices plus configurable display conversion
- Listing creation, editing, deletion, search, filters, and saved listings API
- Participant-only conversations and messages
- Offers, seller acceptance/decline/counter, and two-party deal completion
- Django admin and deterministic demo data

This MVP does not process payments, promise escrow/Buyer Protection, fetch live exchange rates, or book delivery.

## Backend

```bash
cd /Users/waiyanaung/Documents/August2026/PokeFind/PokeFind_APP
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py seed_demo
.venv/bin/python backend/manage.py runserver
```

API health: `http://localhost:8000/api/health/`

Demo accounts (password for both: `PokeFind123!`):

- `seller@pokefind.local`
- `buyer@pokefind.local`

## Frontend

```bash
cd /Users/waiyanaung/Documents/August2026/PokeFind/PokeFind_APP/frontend
pnpm install
pnpm dev
```

Open `http://localhost:5173`. Copy `.env.example` to `.env` only when the API uses a different address.

## Verification

```bash
cd /Users/waiyanaung/Documents/August2026/PokeFind/PokeFind_APP
.venv/bin/python backend/manage.py test accounts.tests common.tests marketplace.tests messaging.tests
cd frontend
pnpm test
pnpm build
```

## Production configuration

The backend uses SQLite when `POSTGRES_DB` is unset. Set the `POSTGRES_*` variables from `backend/.env.example` for PostgreSQL. Put media on S3-compatible storage before deployment; local media storage is development-only. Replace the development secret, disable debug, restrict allowed hosts/CORS, and serve both applications behind HTTPS.
