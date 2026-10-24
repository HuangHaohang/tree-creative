# syntax=docker/dockerfile:1.7

FROM node:26.12.0-bookworm-slim AS builder
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.11.0 --activate
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY frontend/package.json ./frontend/package.json
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
  pnpm config set store-dir /pnpm/store && \
  pnpm install --frozen-lockfile --filter @tree-creative/frontend...
COPY frontend ./frontend
RUN pnpm --dir frontend build

FROM caddy:2.10.2-alpine AS runtime
COPY frontend/Caddyfile /etc/caddy/Caddyfile
COPY --from=builder /workspace/frontend/dist /srv
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["wget", "--quiet", "--tries=1", "--spider", "http://127.0.0.1/healthz"]
