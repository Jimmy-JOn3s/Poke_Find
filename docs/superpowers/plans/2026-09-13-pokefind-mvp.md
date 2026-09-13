# PokeFind MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a locally runnable bilingual Pokemon-card marketplace MVP with React/TypeScript, Django REST, THB/USD support, listings, saved cards, conversations, offers, and completed deals.

**Architecture:** The repository is a monorepo with a Vite React frontend and a Django REST backend. PostgreSQL is production-ready through environment configuration while SQLite keeps local startup immediate. Shared frontend modules own API access, localization, and money formatting; backend services own permissions and offer/deal transitions.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS, Vitest, Django 5.2, Django REST Framework, SimpleJWT, django-cors-headers, Pillow, PostgreSQL-compatible ORM.

---

### Task 1: Establish the monorepo and runnable baselines

**Files:**
- Create: `.gitignore`, `README.md`, `backend/requirements.txt`, `backend/manage.py`, `backend/config/*`
- Import: `frontend/*` from the approved Figma Make export

- [ ] Initialize Git on branch `codex/pokefind-mvp` because the destination is an empty non-repository.
- [ ] Copy the generated React export into `frontend/` and verify `pnpm build` before modifying behavior.
- [ ] Create the Django project, environment settings, CORS configuration, media settings, and health endpoint.
- [ ] Install frontend and backend dependencies and verify both development entrypoints start.

### Task 2: Implement shared account and money foundations with TDD

**Files:**
- Create: `backend/accounts/models.py`, `backend/accounts/serializers.py`, `backend/accounts/views.py`, `backend/accounts/urls.py`
- Create: `backend/common/money.py`, `backend/common/tests/test_money.py`
- Create: `backend/accounts/tests/test_auth_api.py`

- [ ] Write failing tests proving registration returns tokens/profile, `/me/` requires authentication, profile preferences support `th|en` and `THB|USD`, and conversion preserves decimal precision.
- [ ] Run the focused tests and confirm they fail because the API/domain functions do not exist.
- [ ] Implement the custom user profile, JWT endpoints, preference validation, and Decimal-based conversion helper.
- [ ] Run the focused tests and full Django suite until green.

### Task 3: Implement listing catalogue and saves with TDD

**Files:**
- Create: `backend/marketplace/models.py`, `backend/marketplace/serializers.py`, `backend/marketplace/views.py`, `backend/marketplace/urls.py`
- Create: `backend/marketplace/tests/test_listings_api.py`

- [ ] Write failing API tests for public active-list browsing, structured filters, authenticated creation, owner-only mutation, sold status, image-ready fields, and idempotent save/unsave.
- [ ] Run the tests and confirm expected failures.
- [ ] Implement normalized listing status/language/condition/rarity/currency choices, API serializers, filter/query logic, permissions, and save action.
- [ ] Run focused and full backend tests until green.

### Task 4: Implement conversations, offers, and deal completion with TDD

**Files:**
- Create: `backend/messaging/models.py`, `backend/messaging/serializers.py`, `backend/messaging/services.py`, `backend/messaging/views.py`, `backend/messaging/urls.py`
- Create: `backend/messaging/tests/test_deal_flow_api.py`

- [ ] Write failing tests for participant-only conversation access, messages, same-currency offers, seller-only accept/decline, counter-offer linkage, accepted deal creation, and two-party completion.
- [ ] Run the tests and confirm failures are caused by missing behavior.
- [ ] Implement models, thin API views, and centralized transition services with database transactions and uniqueness constraints.
- [ ] Run focused and full backend tests until green.

### Task 5: Add bilingual/currency frontend foundations with TDD

**Files:**
- Create: `frontend/src/lib/api.ts`, `frontend/src/lib/money.ts`, `frontend/src/lib/storage.ts`
- Create: `frontend/src/i18n/catalog.ts`, `frontend/src/i18n/I18nProvider.tsx`
- Create: `frontend/src/lib/money.test.ts`, `frontend/src/i18n/catalog.test.ts`
- Modify: `frontend/package.json`, `frontend/src/main.tsx`

- [ ] Add Vitest and write failing tests for THB/USD formatting, configurable conversion, locale fallback, and complete key parity between Thai and English.
- [ ] Run tests and confirm expected failures.
- [ ] Implement one typed API client, one money utility, one preference store, and one translation catalogue/provider.
- [ ] Run frontend tests and build until green.

### Task 6: Connect the generated UI to the backend

**Files:**
- Modify: `frontend/src/App.tsx`, `frontend/src/pages/*`, `frontend/src/components/*`, `frontend/src/types.ts`
- Create: `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/useListings.ts`
- Create: `frontend/src/components/Price.tsx`, `frontend/src/components/LocaleCurrencySwitcher.tsx`, `frontend/src/components/AsyncState.tsx`

- [ ] Replace page-local duplicated formatting and copy with shared components/catalogue.
- [ ] Connect registration/login/profile preferences and persist JWT locally.
- [ ] Connect listing browse/filter/detail/create/edit/save flows.
- [ ] Connect conversations, messages, offers, accept/decline/counter, and completion confirmation.
- [ ] Preserve the Figma visual language while providing accessible labels, empty states, loading states, and API error states.
- [ ] Run frontend tests and build after each connected vertical slice.

### Task 7: Seed, document, and verify the complete MVP

**Files:**
- Create: `backend/marketplace/management/commands/seed_demo.py`
- Modify: `README.md`

- [ ] Add deterministic demo users, Thai/English listings, a conversation, and offer/deal examples.
- [ ] Document setup, environment variables, demo credentials, migrations, seeding, tests, and development commands.
- [ ] Run migrations from a clean SQLite database, seed data, backend tests, frontend tests, and production frontend build.
- [ ] Start both servers and smoke-test health, registration, listing browse, and frontend rendering.
