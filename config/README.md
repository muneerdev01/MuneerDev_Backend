# Configuration

Runtime settings are loaded from the process environment, or from the
repository-root `.env` file for local development. Start with the root
[`.env.example`](../.env.example); it contains placeholders only.

Production secrets must be configured in the Render environment panel. Do not
put credentials in source files, Vercel `NEXT_PUBLIC_*` variables, or committed
environment files. `APP_ENV=production` disables localhost CORS origins.
