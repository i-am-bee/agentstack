FROM node:22-alpine3.22 AS base
COPY --chown=guest:guest ./apps/agentstack-ui/.next/standalone /workspace/
COPY --chown=guest:guest ./apps/agentstack-ui/.next/static /workspace/apps/agentstack-ui/.next/static
COPY --chown=guest:guest ./apps/agentstack-ui/public /workspace/apps/agentstack-ui/public
RUN mkdir -p /providers
USER guest
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=8334 \
    HOSTNAME="0.0.0.0"
CMD ["node", "/workspace/apps/agentstack-ui/server.js"]
EXPOSE 8334
