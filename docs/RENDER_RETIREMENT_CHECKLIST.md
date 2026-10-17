# Render and PostgreSQL retirement checklist

Do not shut down or delete anything until this list is explicitly approved.

## Still live

- Frontend: https://kings-grillz.onrender.com
- Backend: https://kings-grillz-api.onrender.com
- PostgreSQL on Render (customer and order history)
- Database expiry previously noted: 15 November 2026

## Before any shutdown

1. Export the production PostgreSQL database to a local `.dump` or `.sql` file.
2. Store that export outside Render (computer and a second copy).
3. Confirm the export opens and contains customers, orders and payments.
4. Confirm Receipt Studio does not need those services. It does not.
5. Confirm no staff still use the website or the old SmartPOS apps.
6. Write down the Render service names and the database name.

## Shutdown order, only after approval

1. Suspend or delete the web service `kings-grillz`.
2. Suspend or delete the API service `kings-grillz-api`.
3. Keep the PostgreSQL instance until the export is verified.
4. Only then delete the PostgreSQL instance.
5. Keep the local export permanently.

## Do not delete

- The GitHub repository
- Branch `archive/smartpos-cloud-2026-10-17`
- Tag `archive-smartpos-cloud-2026-10-17`
- The local database export
- Receipt Studio Windows or Android data
