# MuneerDev API

FastAPI backend for the blog, portfolio, admin API, and digital-product checkout.
This repository does not contain the Next.js frontend; frontend routes and
responsive layouts must be verified in the separate Vercel project.

## Local configuration

1. Copy `.env.example` to `.env`.
2. Replace every `REPLACE_*`, `PROJECT_REF`, and database placeholder with
   development credentials. Use Stripe **test** keys only.
3. Install dependencies with `pip install -r requirements.txt`.
4. Before migrating, resolve the schema/migration deployment gate below.
5. Start the API with `uvicorn main:app --reload`.
6. Create a JWT by logging in at `/api/v1/auth/login`. Send it as
   `Authorization: Bearer <token>` to all admin write routes.
7. Create a public `projects` bucket for preview images, a private `products`
   bucket for paid files, and the configured `media` bucket for article media.

Never commit `.env`, paste credentials into source control, or expose the
Supabase service-role, Stripe secret, webhook-signing, Resend, database, or JWT
secrets to browser code.

## Stripe test-mode verification

Before enabling live payments, complete these steps against a non-production
database and test-mode Stripe account:

1. Set Render/development `STRIPE_SECRET_KEY` to the Stripe test secret key.
   Set `FRONTEND_URL` and `ALLOWED_ORIGINS` to the test frontend.
2. Install and authenticate the Stripe CLI. Run
   `stripe listen --forward-to http://localhost:8000/api/webhooks/stripe` and
   put the CLI-generated webhook signing secret in `STRIPE_WEBHOOK_SECRET`.
   For a deployed test service, create a test-mode webhook endpoint at
   `https://<api-domain>/api/webhooks/stripe` and use that endpoint's signing
   secret instead.
3. Configure an active product using the authenticated product admin API.
   Upload its PDF/ZIP through `/api/upload` with `file_type=product_file`, and
   save the returned private `file_path` on the product. The checkout request
   contains only the product slug and buyer email; the API takes the amount
   from the database product record.
4. Start checkout and pay with Stripe test card `4242 4242 4242 4242`, a future
   expiry date, and any CVC. Verify Stripe shows the completed test payment,
   the signed webhook receives HTTP 200, the order becomes `PAID`, and one
   download token is created.
5. Check Resend's test/delivery logs for the email, open the download link,
   and verify the private object can be retrieved. A link must stop working
   at or after 24 hours; the signed storage URL itself is short-lived too.
6. Test declines with Stripe's documented declined test card (for example
   `4000 0000 0000 0002`). Replay the same webhook event from the Stripe
   Dashboard/CLI and confirm there is still one paid order/token and no
   duplicate sales increment. Verify an expired token returns HTTP 410.
7. Call every admin write endpoint without a bearer token and with an
   insufficient-role token; requests must be rejected. Attempt an `.exe`
   upload under both image and product upload types; both must be rejected.
8. Verify the public product list omits inactive products, valid project/product
   pages return the correct data, and unknown slugs return HTTP 404.

Do not promote test objects or test credentials to production. Test-mode data
and live-mode data are separate in Stripe.

## Go live safely

1. Complete the test-mode checks above and review Stripe webhook delivery logs
   for signature errors, repeated failures, and unexpected events.
2. Create a production Stripe webhook endpoint at
   `https://<api-domain>/api/webhooks/stripe` for the event types handled by the
   deployed API: `checkout.session.completed`,
   `checkout.session.async_payment_succeeded`,
   `checkout.session.async_payment_failed`, and `checkout.session.expired`.
   Copy its **live-mode** signing secret separately from the test-mode
   signing secret.
3. In Render, configure production-only environment variables:
   `DATABASE_URL`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_USERNAME`,
   `ADMIN_PASSWORD`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
   `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `RESEND_API_KEY`,
   `RESEND_FROM_EMAIL`, `FRONTEND_URL`, `APP_URL`, `APP_ENV=production`,
   `ALLOWED_ORIGINS`, and `CORS_ALLOW_CREDENTIALS=false`. Use fresh, unique
   secrets and a least-privilege PostgreSQL user. Apply database migrations and
   the RLS lockdown SQL before accepting orders.
4. In the Vercel project, set the frontend's documented public API base URL
   (for example `NEXT_PUBLIC_API_BASE_URL=https://<api-domain>`) and other
   genuinely public frontend settings. Confirm the exact variable name in the
   separate Next.js repository. Never set a Stripe secret, Supabase service-role
   key, database URL, admin password, or webhook secret as a `NEXT_PUBLIC_*`
   variable.
5. Set `STRIPE_SECRET_KEY` to the live secret and `STRIPE_WEBHOOK_SECRET` to
   the live endpoint signing secret in Render. Confirm the endpoint is in
   **live mode** and deliver a controlled low-value real transaction before
   opening sales. Use Stripe's refund process if appropriate.
6. Point the API and website DNS records to Render and Vercel respectively.
   Wait for both platforms to issue valid TLS certificates; force HTTPS and
   confirm the canonical domain, redirects, and HSTS behavior.
7. Verify production CORS allows only the exact website origins, test an
   authenticated admin operation, make a real checkout, verify the webhook,
   confirm email delivery and a private download, and confirm the order total
   matches the database price.
8. Set a rollback plan: disable checkout or revert to maintenance mode rather
   than placing test credentials in a live deployment. Keep database backups
   and rotate credentials immediately if they are exposed.

## Monitoring checklist

- **Render:** inspect the service's Logs tab and deployment events for startup
  failures, database connection errors, 4xx/5xx spikes, webhook failures, and
  email/storage errors. Alert on repeated failed health checks and restart
  loops. Do not log secrets or full payment payloads.
- **Stripe:** review Developers → Webhooks for delivery attempts, response
  codes, signature failures, latency, and retry volume; review Payments for
  failed, disputed, or unexpectedly large transactions. Keep test and live
  dashboards distinct.
- **Supabase:** monitor Storage usage and bandwidth, database usage, backups,
  and API logs. Confirm the `products` bucket is private and public assets do
  not contain purchase files.
- **Resend:** monitor delivery, bounce, complaint, and suppression events; keep
  the sender domain's SPF/DKIM/DMARC records valid.
- **Operations:** review admin/audit activity, dependency/security advisories,
  database backup restoreability, and secret rotation status on a schedule.

## Scope and deployment gate

The checks requiring deployed PostgreSQL, Stripe, Supabase, Resend, Render, or
Vercel credentials cannot be executed from this repository workspace. This
backend repository also does not contain the Next.js frontend, so frontend
visual/responsive checks are not represented by the backend test results.
Do not treat a successful local import or unit test as proof of live-payment
readiness.

**Database deployment is currently blocked:** this repository has no
`alembic.ini` or Alembic `env.py`, and revision `20261006_001` points to an
initial revision that is not present. The standalone Supabase schema also
defines different `products` and `projects` columns than the SQLAlchemy models
used by FastAPI (for example, cents/status columns versus decimal price/active
fields). Reconcile the deployed database, model, and migration baseline before
running migrations or accepting payments. Apply `server/db/rls_lockdown.sql`
to an existing Supabase schema after reviewing it against that database.
