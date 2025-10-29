FROM node:22-alpine AS base
COPY --chown=guest:guest ./apps/agentstack-web/.next/standalone /workspace/
COPY --chown=guest:guest ./apps/agentstack-web/.next/static /workspace/apps/agentstack-web/.next/static
COPY --chown=guest:guest ./apps/agentstack-web/public /workspace/apps/agentstack-web/public
USER guest
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"
CMD ["node", "/workspace/apps/agentstack-web/server.js"]
EXPOSE 3000
