FROM alpine:3.23@sha256:25109184c71bdad752c8312a8623239686a9a2071e8825f20acb8f2198c3f659
# renovate: datasource=npm depName=supergateway
ARG SUPERGATEWAY_VERSION=3.4.3
RUN apk add --no-cache nodejs npm kubectl && npm install -g supergateway@${SUPERGATEWAY_VERSION}
