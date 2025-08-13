FROM node:22-alpine AS base
COPY --chown=guest:guest ./apps/beeai-ui/.next/standalone /workspace/
COPY --chown=guest:guest ./apps/beeai-ui/.next/static /workspace/apps/beeai-ui/.next/static
COPY --chown=guest:guest ./apps/beeai-ui/public /workspace/apps/beeai-ui/public
RUN mkdir -p /providers
USER guest
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=8334 \
    HOSTNAME="0.0.0.0"
CMD ["node", "/workspace/apps/beeai-ui/server.js"]
EXPOSE 8334
