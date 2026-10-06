FROM node:24-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# adapter-auto can't emit a standalone Node server. Swap in adapter-node for the
# image build only (keeps package.json / svelte.config.js unchanged locally).
RUN npm install --no-save @sveltejs/adapter-node@^5 \
    && sed -i "s#@sveltejs/adapter-auto#@sveltejs/adapter-node#" svelte.config.js

# Vite env vars are baked in at build time
ARG VITE_API_BASE_URL=
ARG VITE_WS_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_WS_BASE_URL=$VITE_WS_BASE_URL

RUN npm run build && npm prune --omit=dev

FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=3000 HOST=0.0.0.0

COPY --from=build /app/build ./build
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json .

EXPOSE 3000
CMD ["node", "build"]
