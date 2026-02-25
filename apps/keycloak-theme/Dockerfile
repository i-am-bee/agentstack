FROM quay.io/keycloak/keycloak:26.5.4@sha256:ae8efb0d218d8921334b03a2dbee7069a0b868240691c50a3ffc9f42fabba8b4
WORKDIR /opt/keycloak
COPY dist_keycloak/keycloak-theme-for-kc-all-other-versions.jar /opt/keycloak/providers/keycloak-theme.jar
RUN /opt/keycloak/bin/kc.sh build
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]