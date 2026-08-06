# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases will use semantic versioning unless the release policy defines a stricter scheme.

## [Unreleased]

### Added

- Repository governance and project foundation.
- Umi Max and Ant Design Pro frontend foundation.
- FastAPI modular backend with health checks, observability, Celery workers, and pluggable identity-provider ports.
- MySQL, Redis, MinIO, API, workers, and frontend Docker Compose stack.
- Frontend, backend, and Compose GitHub Actions quality gates.
- WPS SSO gateway adapter, single-use login state, Redis-backed browser sessions, current-user and real server-side logout APIs.
- Internal users, external WPS identity bindings, authentication audit events, masked department tree, personnel list and search APIs.
- Frontend session restoration, WPS login/logout controls, global 401 handling, and organization directory page.
- Standalone responsive login page, protected business routes, and safe post-login return paths.

### Changed

### Deprecated

### Removed

### Fixed

### Security

- WPS client credentials and token envelopes remain server-side; browser sessions use opaque `HttpOnly`, `SameSite=Lax` cookies and CSRF-protected logout.
