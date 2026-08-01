# Technology Stack

This document records the approved baseline technology stack. Agents should use these choices by default and must not replace a core technology without an explicit project decision.

## Frontend

- Language: TypeScript.
- Runtime: a pinned Node.js LTS release.
- Package manager: pnpm with a committed lockfile.
- Application framework: Umi Max.
- UI runtime: React.
- Design system: Ant Design and Ant Design Pro / ProComponents.
- Charts: Apache ECharts.
- Graph visualization: AntV G6.
- Unit and component testing: Vitest and React Testing Library.
- End-to-end testing: Playwright.
- Code quality: ESLint, Prettier, and TypeScript strict mode, using Umi defaults where available.
- Supporting libraries: select task-specific libraries only when needed; prefer the Umi Max and Ant Design ecosystems before adding overlapping alternatives.

Expected supporting categories include:

- HTTP client and API typing.
- Server-state caching and request lifecycle management.
- Form validation.
- Date and time handling.
- Utility functions.
- Testing and browser automation.
- Code formatting and static analysis.

Do not select a package for an undecided category until its requirements are clear. Once selected, record it in this document.

## Backend

- Language/runtime: Python 3; pin the project Python version during scaffolding.
- Dependency and virtual-environment manager: uv with a committed lockfile.
- API framework: FastAPI.
- Validation and configuration: Pydantic and Pydantic Settings.
- Relational database: MySQL with SQLAlchemy 2.x.
- Database migrations: Alembic.
- Cache, distributed coordination, and ephemeral state: Redis.
- Object storage: MinIO using S3-compatible APIs.
- Agent and workflow orchestration: LangGraph.
- Browser automation: Playwright.
- Unit and integration testing: pytest and pytest-asyncio.
- Code quality: Ruff and mypy.

The backend should expose an explicit API contract consumed by the frontend. Prefer generated or contract-checked client types over manually duplicated request and response models.

## Background Jobs and Workers

LangGraph workflows and other long-running or retryable operations must not run in the API request process.

- Use a Redis-backed durable task queue with separately deployable worker processes.
- Use Celery as the default queue and worker implementation unless a proven project constraint requires another implementation.
- Separate queues by workload where useful, especially for LangGraph execution, browser automation, and general background jobs.
- Assign every accepted job a stable identifier and expose status, progress, result, cancellation, and failure information through the API.
- Keep durable business state and audit history in MySQL or the selected LangGraph persistence store. Redis queue state alone is not the system of record.
- Make retryable jobs idempotent. Configure bounded retries, exponential backoff, timeouts, concurrency, and dead-letter or failed-job handling.
- Run Playwright work in dedicated workers with explicit CPU, memory, browser concurrency, download, filesystem, and network restrictions.

## Authentication and Authorization

Authentication must use a ports-and-adapters design. Domain and application code depend only on a normalized internal identity and authorization interface, never directly on a specific SSO vendor or protocol SDK.

### Core Model

- Maintain an internal user record and stable internal user ID independent of external identity providers.
- Normalize successful authentication into a common principal containing the internal user ID, external identity reference, tenant or organization where applicable, and normalized claims.
- Link external identities through a dedicated identity-binding table keyed by provider and provider subject. Do not use email alone as an immutable identity key.
- Keep authentication, session/token handling, user provisioning, and authorization as separate concerns.

### Login and Tokens

- Provide a local-login adapter where first-party username or email and password login is required.
- Use secure, `HttpOnly`, `SameSite` cookies backed by Redis sessions as the default browser login mechanism.
- Support short-lived JWT bearer tokens for service-to-service, CLI, or explicitly required API access. Define issuer, audience, expiry, rotation, revocation, and signing-key rules.
- Do not store long-lived authentication tokens in browser local storage.

### SSO Adapters

- Define a stable `IdentityProvider` or equivalent interface for login initiation, callback handling, claims normalization, logout, and optional token refresh.
- Implement OpenID Connect as the first generic SSO adapter. Add vendor-specific OIDC adapters only for provider quirks or additional capabilities.
- Allow future SAML 2.0 or other enterprise SSO adapters without changing domain services, RBAC evaluation, or the internal user model.
- Load provider configuration through environment or secret management and a provider registry. Do not scatter provider conditionals through routes or business code.
- Make account linking, just-in-time provisioning, disabled-user handling, claim mapping, and logout behavior explicit per adapter.

### RBAC

- Store application roles, permissions, scopes, and assignments in the application database rather than treating SSO claims as the only authority.
- Map trusted external groups or claims to internal roles through configurable rules.
- Enforce permissions in backend application/service boundaries; frontend checks are for user experience only.
- Default to least privilege and deny access when no rule grants it.
- Record security-relevant events such as login, logout, failed authentication, identity linking, role changes, and sensitive actions in an audit log.

## Operations and Delivery

- Source hosting and collaboration: GitHub.
- CI/CD: GitHub Actions.
- UAT environment: Docker on the local machine.
- Production environment: Docker on the remote host available through the local SSH alias `server244`.
- Deployment unit: a project-specific Docker Compose stack, isolated from other projects.
- Reverse proxy and HTTPS: Caddy as the default edge proxy, with automated certificate renewal when public DNS is available.

Each environment must use separate configuration, credentials, storage, database names, network names, and Compose project names. Secrets must not be committed to the repository or embedded in images.

Production deployment must be reproducible from versioned Dockerfiles and Compose configuration. Do not make undocumented changes directly inside running containers.

## Repository Shape

The exact repository layout is not decided. Unless project constraints require separate repositories, prefer a monorepo with clear boundaries such as:

```text
frontend/       # Umi Max application
backend/        # FastAPI application
deploy/         # Docker Compose and environment deployment assets
scripts/        # Repeatable development and operations scripts
tests/          # Cross-service or end-to-end tests, when applicable
```

This is a starting convention, not authorization to scaffold these directories before the project structure is requested.

## Architecture and Engineering Defaults

- API: versioned REST endpoints documented through OpenAPI. Use Server-Sent Events for one-way workflow progress streaming; introduce WebSocket only for genuinely bidirectional real-time features.
- API conventions: define one shared approach for pagination, error envelopes, idempotency, rate limits, and request correlation IDs.
- LangGraph persistence: use a durable checkpointer and explicitly define conversation-state retention and recovery. Do not rely on in-process memory in deployed environments.
- Data access: use explicit transaction boundaries, bounded connection pools, and migrations that support a documented rollback or forward-fix plan.
- Redis: namespace keys by project, environment, and subsystem; define TTL and persistence expectations for each key family.
- MinIO: define bucket layout, object naming, upload limits, lifecycle, retention, and access policies before implementing uploads.
- Security: manage secrets outside Git; configure CORS, CSRF protection, content-security policy, dependency scanning, and container image scanning.
- CI: require formatting, linting, type checking, tests, builds, and migration validation before deployment.
- Releases: use versioned images and a documented deployment, migration, health-check, rollback, and hotfix process.
- Observability: emit structured logs and correlation IDs; provide health/readiness endpoints, metrics, alerting, error tracking, and distributed tracing.
- Reliability: configure resource limits, restart policies, graceful shutdown, timeouts, retries, and backup/restore procedures. Test MySQL and MinIO restoration periodically.

## Remaining Environment-Specific Decisions

These values depend on infrastructure or product requirements and must be recorded when known:

- Exact Node.js, Python, database, Redis, MinIO, browser, and direct dependency versions.
- Production domain names, DNS, TLS exposure, ports, and network policy.
- Initial SSO providers, their protocols and claim mappings, and local-login availability.
- Initial roles, permissions, tenant model, administrator bootstrap, and audit retention.
- Backup destinations, retention periods, recovery objectives, alert destinations, and incident contacts.
- LangGraph checkpoint implementation and data-retention duration.

## Version Policy

Exact versions have not been selected yet. During scaffolding:

- Pin runtime and direct dependency versions through manifests and lockfiles.
- Prefer currently supported stable releases that are mutually compatible.
- Record Node.js, Python, MySQL, Redis, MinIO, and Playwright runtime versions here.
- Upgrade intentionally through reviewed pull requests, with tests and migration notes where relevant.
