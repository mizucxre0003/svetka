# ─────────────────────────────────────────────────────────
#  STAGE 1: Build Admin Panel
# ─────────────────────────────────────────────────────────
FROM node:20-alpine AS admin-builder
WORKDIR /build
COPY admin-panel/package*.json ./
RUN npm ci --prefer-offline
COPY admin-panel/ ./
# API вызовы идут через nginx на том же домене — используем относительные URL
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build

# ─────────────────────────────────────────────────────────
#  STAGE 2: Build Mini App
# ─────────────────────────────────────────────────────────
FROM node:20-alpine AS mini-builder
WORKDIR /build
COPY mini-app/package*.json ./
RUN npm ci --prefer-offline
COPY mini-app/ ./
ENV NEXT_PUBLIC_MINI_APP_API_URL=""
RUN npm run build

# ─────────────────────────────────────────────────────────
#  STAGE 3: Runtime (Python + Node + nginx + supervisord)
# ─────────────────────────────────────────────────────────
FROM python:3.12-slim

# System deps: nginx, supervisord, Node.js 20
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor curl gnupg2 ca-certificates \
    gcc libpq-dev && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/log/supervisor

# ── Backend ───────────────────────────────────────────────
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# ── Bot ───────────────────────────────────────────────────
WORKDIR /app/bot
COPY bot/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY bot/ ./

# ── Admin Panel (Next.js standalone) ─────────────────────
COPY --from=admin-builder /build/.next/standalone /app/admin
COPY --from=admin-builder /build/.next/static     /app/admin/.next/static
RUN mkdir -p /app/admin/public

# ── Mini App (Next.js standalone) ────────────────────────
COPY --from=mini-builder /build/.next/standalone /app/mini
COPY --from=mini-builder /build/.next/static     /app/mini/.next/static
RUN mkdir -p /app/mini/public

# ── nginx ─────────────────────────────────────────────────
COPY deploy/nginx.conf /etc/nginx/nginx.conf

# ── supervisord ───────────────────────────────────────────
COPY deploy/supervisord.conf /etc/supervisor/conf.d/svetka.conf

# Koyeb слушает один порт
EXPOSE 8080

CMD bash -c "cd /app/backend && alembic upgrade head && exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf"
