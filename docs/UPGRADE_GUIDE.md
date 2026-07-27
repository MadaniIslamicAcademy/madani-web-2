# Upgrade Guide

## Before changing code

1. Create a feature branch.
2. Read the current model and service boundaries.
3. Add or update tests first.
4. Never place provider HTTP calls in a route file.
5. Never expose provider tokens to the frontend.

## Adding a new social platform

1. Add a value to `SocialProvider`.
2. Create an adapter in `app/providers`.
3. Register it in `app/providers/factory.py`.
4. Add provider metadata validation.
5. Add a frontend option in the connections page.
6. Add tests using mocked HTTP responses.
7. Document the required permissions.

## Adding campaign fields

1. Update the SQLAlchemy model.
2. Update Pydantic schemas.
3. Create and review an Alembic migration.
4. Update frontend types and forms.
5. Add API and UI tests.

## Replacing the AI provider

Implement the `ContentGenerator` protocol in `app/services/ai.py`. The rest of the system expects normalized platform content and should not depend on a specific model vendor.

## Changing the scheduler

The current scheduler uses Celery Beat. A managed scheduler can replace it by calling the same `enqueue_due_posts` task. Do not duplicate publishing logic in the scheduler.

## Database changes

Never edit production tables manually. Use Alembic migrations and take a backup before destructive changes.

## Versioning

Use semantic versions:

• Patch for fixes
• Minor for backward compatible features
• Major for breaking API or schema changes
