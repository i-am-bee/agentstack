FROM alpine:3.23@sha256:25109184c71bdad752c8312a8623239686a9a2071e8825f20acb8f2198c3f659 AS base
RUN apk add --no-cache nodejs
COPY --chown=guest:guest ./apps/beeai-web/.next/standalone /workspace/
COPY --chown=guest:guest ./apps/beeai-web/.next/static /workspace/apps/beeai-web/.next/static
COPY --chown=guest:guest ./apps/beeai-web/public /workspace/apps/beeai-web/public
USER guest
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"
CMD ["node", "/workspace/apps/beeai-web/server.js"]
EXPOSE 3000
