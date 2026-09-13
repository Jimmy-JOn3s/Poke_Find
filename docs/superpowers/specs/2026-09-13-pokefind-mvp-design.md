# PokeFind MVP Design

## Objective

Build a runnable mobile-first Pokemon TCG marketplace MVP for Thailand. The MVP will reuse the Figma Make React interface as its visual starting point and replace mock state with a Django REST API. It will support Thai and English interface copy, and listing prices in Thai baht (THB) and US dollars (USD).

## Repository layout

```
PokeFind_APP/
  frontend/    React + TypeScript + Vite application
  backend/     Django + Django REST Framework API
  docs/        product and implementation documents
```

The existing Figma Make export at `/Users/waiyanaung/Downloads/PokeFind` will be copied into `frontend/` as the initial UI. The new backend will expose JSON APIs under `/api/`.

## MVP workflows

1. A user registers, signs in, selects Thai or English, and has a personal or business seller profile.
2. An authenticated seller creates, edits, publishes, and marks a listing sold. A listing contains its Pokemon-card attributes, price, currency, optional photo, and availability.
3. A buyer searches and filters active listings by text, card language, condition, rarity, and price currency; opens a listing; saves it; and messages the seller.
4. Within a listing conversation, a buyer can make an offer in the listing currency; the seller can accept, decline, or counter it.
5. The seller and buyer can mark an accepted deal completed. The app persists the final price and keeps it separate from the listing asking price.
6. The user can switch the display language and preferred display currency. Currency conversion is illustrative only, using a server-configured exchange rate; the original listing currency and amount remain authoritative.

## Technical architecture

### Frontend

- React, TypeScript, Vite, and the existing Tailwind-based UI export.
- React Router for stable client routes; a thin API client for auth, listings, saved listings, threads, offers, and profile.
- A translation dictionary for `th` and `en`; no hard-coded user-facing strings in page components.
- An app preference store persists language and display-currency selection locally.
- Listing price model always displays an ISO currency code and uses decimal-safe API values; never JavaScript floating-point arithmetic for price calculations.

### Backend

- Django, Django REST Framework, and JWT authentication.
- PostgreSQL in production; local development uses SQLite by default so the MVP runs without infrastructure. Environment configuration selects the database.
- Django apps: `accounts`, `marketplace`, `messaging`, and `common`.
- Local media storage in development and an S3-compatible storage interface through environment configuration for deployment.
- Django admin provides the initial moderation/back-office surface.

### Domain model

- `User` and `Profile`: role, display name, avatar, preferred language, preferred display currency, seller verification state.
- `Listing`: seller, card attributes, description, `asking_price`, `currency`, quantity, status, timestamps, image.
- `SavedListing`: buyer/listing uniqueness constraint.
- `Conversation`: unique buyer + seller + listing thread.
- `Message`: conversation, author, body, message type, timestamp.
- `Offer`: conversation, proposer, amount, currency, status, counter-offer relationship, timestamps.
- `Deal`: accepted offer, completion confirmations, final price/currency, completion timestamp.

## API boundary

- `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/refresh/`, `GET/PATCH /api/auth/me/`
- `GET/POST /api/listings/`, `GET/PATCH/DELETE /api/listings/{id}/`, `POST /api/listings/{id}/save/`
- `GET /api/listings/?q=&language=&condition=&rarity=&currency=&min_price=&max_price=`
- `GET/POST /api/conversations/`, `GET /api/conversations/{id}/messages/`, `POST /api/conversations/{id}/messages/`
- `POST /api/conversations/{id}/offers/`, `POST /api/offers/{id}/accept/`, `POST /api/offers/{id}/decline/`, `POST /api/offers/{id}/counter/`
- `POST /api/deals/{id}/confirm-completion/`

## Deliberate MVP exclusions

- No real payments, escrow, refunds, exchange-rate feed, shipping integration, or Buyer Protection promise.
- No live WebSocket chat: request/refresh chat is sufficient for the MVP; real-time delivery is a follow-up.
- No social login, email delivery, card scanning, public price charts, or automated fraud detection.
- No card-catalogue import; sellers enter the required card fields manually.

## Engineering guardrails

- Follow DRY: extract shared behavior once it is used by more than one screen, endpoint, or workflow. Do not copy/paste components, translations, API calls, validation, or business-state logic.
- Keep one source of truth for each concern: TypeScript domain types mirror the API contract from a single module; API URLs and request helpers live in one typed client; translations live only in locale dictionaries; currency formatting/conversion lives in one money utility; Django permissions and deal/offer state transitions live in domain services.
- Prefer composable, focused units. Shared UI elements such as listing cards, price displays, language/currency pickers, form fields, status badges, dialogs, and loading/error states are reusable components rather than page-local duplicates.
- Pages compose components and hooks; they must not contain repeated fetch, mutation, or formatting code. Feature hooks own query and mutation lifecycle behavior.
- Django views remain thin. Serializers validate representation and input; service functions own state-changing workflows; query functions centralize reusable listing and permission queries.
- Never create a second version of a model, enum, endpoint contract, or translation key to solve a local problem. Extend the existing abstraction or deliberately refactor it.
- Add a test whenever a shared rule is introduced or changed. Reuse factories/fixtures and helper assertions rather than duplicating setup across test modules.
- Use clear names, small modules, and explicit interfaces. Duplication, circular imports, dead code, and placeholder implementations are release blockers.

## Quality gates

- Django tests cover permissions, listing CRUD/search, conversation access, and offer/deal state transitions.
- Frontend build completes and core flows handle Thai and English copy plus THB/USD formatting.
- API never allows a user to modify another user’s listing, conversation, offer, or deal.
- A smoke test demonstrates register -> create listing -> search -> offer -> accept -> complete.

## Implementation order

1. Scaffold backend and copy the frontend export.
2. Implement models, migrations, JWT auth, admin, and listing API.
3. Wire frontend authentication, localization, preferences, and listings/search to the API.
4. Add saved listings, conversations/messages, offers, and completion flow.
5. Seed demo records, run API tests, run frontend build, and document local startup.
