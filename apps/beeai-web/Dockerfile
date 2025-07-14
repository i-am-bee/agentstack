FROM node:22-alpine AS base
COPY --chown=guest:guest ./apps/beeai-web/.next/standalone /workspace/
COPY --chown=guest:guest ./apps/beeai-web/.next/static /workspace/apps/beeai-web/.next/static
COPY --chown=guest:guest ./apps/beeai-web/public /workspace/apps/beeai-web/.next/public
USER guest
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"
CMD ["node", "/workspace/apps/beeai-web/server.js"]
EXPOSE 3000
