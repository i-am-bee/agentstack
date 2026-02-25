FROM alpine:3.23@sha256:25109184c71bdad752c8312a8623239686a9a2071e8825f20acb8f2198c3f659 AS base
RUN apk add --no-cache nodejs
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
