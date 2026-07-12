# Deploying the demo

The demo runs as **one service**: the FastAPI container applies migrations on
boot and serves both the API and the production SPA build (so SSE and the
auth cookie need no proxy configuration). All data stays synthetic.

## Render (recommended — one click from the repo)

1. Push the repository to GitHub.
2. In Render: **New → Blueprint**, pick the repo. `render.yaml` provisions a
   free Postgres and the web service (Docker build from the root
   `Dockerfile`, `JWT_SECRET` generated, `COOKIE_SECURE=true`,
   `DATABASE_URL` wired from the database).
3. After the first deploy, open the service **Shell** and seed once:
   ```bash
   python seed.py
   ```
4. Open the service URL and sign in with a demo account
   (`chen@vitals.test` / `password123`, etc. — the login-page quick-fill
   panel is dev-only and never ships in production builds).

Free-tier notes: the service sleeps after idle (first request takes ~1 min)
and the free Postgres expires after 30 days — fine for an application-season
demo.

## Fly.io (alternative)

```bash
fly launch --no-deploy          # detects the root Dockerfile; pick a region
fly postgres create --name vitals-db
fly postgres attach vitals-db   # sets DATABASE_URL
fly secrets set JWT_SECRET=$(openssl rand -hex 32) COOKIE_SECURE=true
fly deploy
fly ssh console -C "python seed.py"
```

## Any Docker host

```bash
docker build -t vitals .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://user:pass@host:5432/vitals \
  -e JWT_SECRET=$(openssl rand -hex 32) -e COOKIE_SECURE=true vitals
docker exec <container> python seed.py   # once
```

For local development keep using the two dev servers (or `docker compose up`,
which runs the nginx-proxied variant) — see the README.
