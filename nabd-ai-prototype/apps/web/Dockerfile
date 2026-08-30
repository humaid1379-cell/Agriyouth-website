# NABD AI Decision Review - web image.
#
# A static bundle served by nginx as a non-root user. The container makes no outbound
# request of its own: the browser talks to the API through the reverse proxy below, which
# resolves only to the Compose-internal API service.

FROM node:22.12-bookworm-slim AS build

WORKDIR /srv/web

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY tsconfig.json tsconfig.node.json vite.config.ts tailwind.config.js postcss.config.js index.html ./
COPY src ./src
COPY tests ./tests

RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

COPY --from=build /srv/web/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
