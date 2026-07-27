# Architecture

## Design goals

The project is designed around six rules.

1. Social platforms are replaceable adapters.
2. Secrets never reach the browser.
3. Publishing is asynchronous and retryable.
4. Every important action is auditable.
5. AI output requires approval by default.
6. The platform remains useful in mock mode without external accounts.

## Runtime components

### Web application

The Next.js application is the staff dashboard. It handles login, campaign creation, editing, approval, scheduling, connection management, lead review and reports. It never stores provider access tokens.

### API application

FastAPI owns authentication, validation, business rules, database access, AI generation, OAuth callbacks, webhook endpoints and publishing commands.

### Worker

Celery runs long tasks outside web requests. It generates content, publishes posts, processes inbound WhatsApp messages and retries transient failures.

### Scheduler

Celery Beat checks for due approved posts once per minute and places them on the worker queue.

### Database

PostgreSQL stores users, campaigns, posts, provider connections, publishing attempts, admission leads, admission sessions and audit events.

### Queue

Redis transports worker jobs and stores short lived Celery state.

## Provider adapter boundary

Every provider implements the same `publish` method and returns a `PublishResult`. Adding a new social platform therefore requires one adapter plus registration in the adapter factory. Campaign and scheduler code should not contain platform specific HTTP calls.

## Post state machine

```text
DRAFT
  to GENERATED
  to APPROVED
  to SCHEDULED
  to PUBLISHING
  to PUBLISHED
  or FAILED
```

A failed post may return to `SCHEDULED` while retries remain. A user may also return generated or approved content to draft for editing.

## Security boundary

• The web application receives only connection status and account labels.
• Access and refresh tokens are encrypted with Fernet before storage.
• Authentication uses HTTP only cookies and a CSRF token.
• Webhooks are verified by provider specific tokens or signatures where supported.
• Audit logs record actor, action, target and metadata.

## Extending the system

Follow `docs/UPGRADE_GUIDE.md`. New feature code should be added through a service or adapter boundary, not directly inside route handlers.
