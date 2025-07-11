FROM node:23-alpine AS base

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable pnpm

FROM base AS builder
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV API_URL=http://beeai-platform-svc:8333

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm i --frozen-lockfile
RUN pnpm run --filter=@i-am-bee/beeai-ui build
RUN pnpm deploy --legacy --filter=@i-am-bee/beeai-ui --prod /prod/app
RUN cp -r apps/beeai-ui/.next /prod/app/.next

FROM base AS runner
WORKDIR /opt

ENV NODE_ENV=production

ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /prod/app/.next/standalone ./

WORKDIR /opt/apps/beeai-ui

COPY --from=builder --chown=nextjs:nodejs /prod/app/.next/static ./.next/static
COPY --from=builder /prod/app/public ./public

USER nextjs

EXPOSE 3000

ENV PORT=3000

ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
