FROM alpine:3.23
# renovate: datasource=npm depName=supergateway
ARG SUPERGATEWAY_VERSION=3.4.3
RUN apk add --no-cache nodejs npm kubectl && npm install -g supergateway@${SUPERGATEWAY_VERSION}
