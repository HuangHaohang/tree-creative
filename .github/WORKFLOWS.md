# GitHub Actions

The repository CI workflow validates frontend, backend, and Compose changes. No workflow may report success without running meaningful checks.

The delivery pipeline stages are:

1. Repository policy and secret scanning.
2. Frontend lint, type checking, unit tests, and production build.
3. Backend lint, type checking, unit/integration tests, and migration validation.
4. End-to-end or smoke testing for critical paths.
5. Dependency and container image scanning.
6. Versioned image build with provenance metadata.
7. UAT deployment and verification.
8. Protected, auditable production deployment with health checks and rollback.

Use least-privilege workflow permissions, pinned third-party actions, protected environments, concurrency controls, immutable artifacts, and GitHub-managed secrets.
