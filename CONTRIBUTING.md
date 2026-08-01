# Contributing

This is a private, proprietary repository. Contributions require explicit repository access and must follow the controls below.

## Before Development

1. Read `AGENTS.md` and the required files in `agent-guides/`.
2. Confirm the requested behavior, module boundary, acceptance criteria, and security impact.
3. Check for existing modules and maintained libraries before adding new abstractions or dependencies.

## Branches and Commits

- Protect `main`; do not push feature work directly to it.
- Use short-lived branches named `feature/<topic>`, `fix/<topic>`, `refactor/<topic>`, `docs/<topic>`, or `chore/<topic>`.
- Use Conventional Commits, for example `feat(auth): add OIDC provider adapter`.
- Keep commits reviewable and free of generated noise, secrets, credentials, local data, and unrelated changes.

## Pull Requests

- Keep one coherent outcome per pull request.
- Explain the reason, approach, risks, validation, migration impact, and rollback plan.
- Add or update automated tests for behavior changes.
- Update contracts, migrations, configuration examples, documentation, and changelog entries when applicable.
- Obtain required code-owner approval and pass all required checks before merge.
- Use squash merge by default unless preserving commit history has a concrete value.

## Quality Gate

The exact commands will be added after project scaffolding. The required gate is:

1. Formatting and linting.
2. Static type checking.
3. Unit and integration tests.
4. Frontend and backend builds.
5. Migration validation.
6. Dependency, secret, and container image scanning.
7. End-to-end or smoke tests for affected critical paths.

Never bypass a failing gate to make a release appear successful.
