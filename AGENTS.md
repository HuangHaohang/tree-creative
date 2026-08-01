# AGENTS.md

## Scope

This file applies to the entire repository. Add a more specific `AGENTS.md` in a subdirectory only when that area needs different instructions.

## Required Reading

Before starting work, read [`agent-guides/README.md`](agent-guides/README.md). Every development task must also begin by reading [`agent-guides/development-principles.md`](agent-guides/development-principles.md); then read the other guides relevant to the task. Treat those documents as repository-level instructions unless a more specific `AGENTS.md` overrides them.

## Project State

The monorepo foundation is initialized with separate Umi Max frontend, FastAPI backend, Docker Compose deployment, and GitHub Actions CI. Follow `agent-guides/tech-stack.md` and the module-level READMEs when extending it.

## Working Principles

- Read the relevant files and nearby documentation before making changes.
- Keep changes focused on the requested outcome; avoid unrelated refactors.
- Preserve existing behavior unless the task explicitly requires changing it.
- Follow established project conventions once they exist instead of introducing competing patterns.
- Prefer clear, maintainable code over clever abstractions.
- Never commit secrets, credentials, tokens, private keys, or local environment files.
- Do not overwrite or discard user changes. Treat a dirty worktree as intentional unless proven otherwise.
- Avoid destructive commands and broad filesystem operations.

## Dependencies

- Reuse existing dependencies when practical.
- Add a dependency only when it materially simplifies the implementation or improves correctness.
- When adding one, update the appropriate manifest and lockfile together and briefly document why it is needed.
- Do not change package managers or regenerate lockfiles without a task-specific reason.

## Implementation

- Keep public interfaces small and explicit.
- Validate inputs at system boundaries and return actionable errors.
- Handle expected failure modes; do not silently swallow errors.
- Add comments for intent, constraints, and non-obvious tradeoffs—not for code that is already self-explanatory.
- Keep generated files separate from hand-edited source, and use the project generator when one exists.

## Verification

- Run the narrowest relevant checks during development, then the broader available suite before handoff.
- Add or update tests for behavior changes and bug fixes when a test framework exists.
- Verify user-visible changes through the actual interface when practical.
- If a check cannot be run, state exactly which check was skipped and why.
- Do not claim success when tests, builds, or linters are failing.

## Documentation

- Update documentation when setup, behavior, configuration, or public interfaces change.
- Keep examples executable and aligned with the current implementation.
- Record new environment variables in an example environment file using safe placeholder values.

## Handoff

Summarize:

- What changed.
- Which checks were run and their results.
- Any remaining risks, assumptions, or follow-up work.

## Commands

- Setup: `make setup`
- Frontend development: `make dev-frontend`
- Backend development: `make dev-backend`
- Worker development: `make worker`
- Test: `make test`
- Lint: `make lint`
- Type checking: `make typecheck`
- Format: `make format`
- Verify formatting: `make format-check`
- Build: `make build`
- Validate Compose: `make compose-config`
- Start/stop UAT: `make uat-up` / `make uat-down`
