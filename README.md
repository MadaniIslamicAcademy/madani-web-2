# Madani Social Automation Platform

A full stack, extensible social media automation and WhatsApp admissions platform for Madani Islamic Academy Ltd.

## What is included

• Next.js admin dashboard
• FastAPI backend
• PostgreSQL database
• Redis and Celery scheduler
• AI post generation with a template fallback
• Draft, approval, scheduling, publishing, retry and audit history
• Provider adapters for Facebook, Instagram, LinkedIn, WhatsApp, YouTube, TikTok, X and a safe Mock provider
• WhatsApp admissions webhook and lead collection flow
• Docker development environment
• Alembic migrations
• Tests and CI
• Deployment examples and detailed documentation

## Repository layout

```text
apps/
  api/       FastAPI application, worker and migrations
  web/       Next.js admin dashboard
docs/        Architecture, setup, integrations and upgrade guides
infra/       Deployment examples
```

## Quick start with Docker

1. Copy the environment file.

```bash
cp .env.example .env
```

2. Change the bootstrap admin password and encryption key in `.env`.

3. Start the full stack.

```bash
docker compose up --build
```

4. Open the admin dashboard.

```text
http://localhost:3000
```

5. API documentation is available at:

```text
http://localhost:8000/docs
```

## Default safe mode

The platform starts with `SOCIAL_PUBLISH_MODE=mock`. This means approved and scheduled posts are processed normally but no real social account receives a post. Change a connection to an official provider only after its credentials and permissions have been configured.

## Important security rules

• Never commit `.env` or access tokens.
• Provider tokens are encrypted before database storage.
• Fees, discounts, class times and teacher availability are never invented or confirmed by the AI.
• Trial timing is always referred to the Admissions Department.
• The official fee page remains the source of truth.

## Development commands

Backend checks:

```bash
cd apps/api
python -m compileall app
pytest
```

Frontend checks:

```bash
cd apps/web
npm install
npm run lint
npm run build
```

See `docs/SETUP.md` for the full setup and `docs/UPGRADE_GUIDE.md` before adding new features.
