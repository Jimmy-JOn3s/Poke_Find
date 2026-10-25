# Verify price-data snapshots

The `feat/price-data` branch records the agreed price/currency and the listing's
card name, set, and condition when a deal opens. A price observation becomes a
completed trade only after both parties confirm, which sets `completed_at`.
Pending and cancelled deals must be excluded from any future market-price query.
This branch does not add a market-price endpoint or analytics calculations.

## Automated checks

From the repository root, with the local backend environment configured:

```bash
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py test messaging.tests marketplace.tests.test_seed_demo --noinput
.venv/bin/python backend/manage.py makemigrations --check --dry-run
```

Tests cover direct reservations, accepted offers, listing edits, protected
deletion, legacy backfill, completion timestamps, and read-only admin fields.
Django creates a separate test database; the local PostgreSQL role needs
`CREATEDB` for these tests. Do not grant that privilege to production app roles.

## Manual check

1. Run the backend and frontend using the README instructions. Sign in as the
   demo seller (`seller@pokefind.local`) and buyer (`buyer@pokefind.local`) in
   separate browser sessions. Use your configured demo password.
2. Start a conversation about an active listing. Make an offer as the buyer and
   accept it as the seller, or reserve directly from seller chat.
3. Open Django admin's **Deals** list as a staff user. The card name, set,
   condition, and agreed price should match the deal, not necessarily the asking
   price. The snapshot fields are read-only in admin.
4. Confirm completion as one party: the deal should remain accepted. Confirm as
   the other party: it should become completed with a completion date.
5. In a business user's profile, open Analytics. It should show localized
   “Coming soon” text without fabricated revenue or sales figures.

Inspect completed observations directly if needed:

```bash
.venv/bin/python backend/manage.py shell -c "from messaging.models import Deal; print(list(Deal.objects.filter(status=Deal.Status.COMPLETED).values('card_name', 'card_set', 'condition', 'final_price', 'currency', 'completed_at')))"
```

## Limits

- Migration `0007` fills older deals using current listing details. It cannot
  reconstruct historical edits; backfilled records are best-effort snapshots.
- Existing deal/offer relationships protect traded listings from deletion.
  This branch does not make deals independent of those relationships.
- Read-only admin fields and the service flow protect normal edits, but snapshots
  are not immutable at the database level; direct ORM/SQL updates can change them.
- Demo trades are synthetic. They must not be presented as real market observations.
- Name/set/condition alone do not uniquely identify a collectible. A future market
  dataset needs card number, print language, variant/grading, quantity, provenance,
  and a policy for currencies and potentially fraudulent trades before aggregation.
