# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import os
import socket
import sys

from beeai_server.configuration import Configuration, get_configuration

# configure logging before importing anything
from beeai_server.logging_config import configure_logging

configure_logging()

from beeai_server.telemetry import configure_telemetry  # noqa: E402

configure_telemetry()

logger = logging.getLogger(__name__)

configuration: Configuration = get_configuration()

JWKS_URL = None

if not configuration.auth.disable_auth:
    JWKS_URL = configuration.auth.jwks_url

configuration: Configuration = get_configuration()

JWKS_URL = None

if not configuration.auth.disable_auth:
    JWKS_URL = configuration.auth.jwks_url


def serve():
    config = get_configuration()
    host = "0.0.0.0"

    if sys.platform == "win32":
        logger.error("Native windows is not supported, use WSL")
        return

    # Download the public jwk key set (jwks)
    if JWKS_URL is not None:
        os.spawnl(os.P_WAIT, "/usr/bin/wget", "/usr/bin/wget", JWKS_URL, "-O", "/jwks/pubkeys.json")
        logger.info("Public keys downloaded from jwks endpoint OK")
        # extract the ingestion pem from the key
        rc = os.spawnl(
            os.P_WAIT,
            "/usr/bin/openssl",
            "/usr/bin/openssl",
            "rsa",
            "--in",
            "/etc/config/ingestion.key",
            "--pubout",
            "-out",
            "/jwks/ingestion.pem",
        )
        logger.info("openssl pubout rc: %s", str(rc))
    else:
        logger.warning("JWKS_URL environment variable is None. OAuth will be disabled")

    with socket.socket(socket.AF_INET) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, config.port))
        except OSError:  # pragma: full coverage
            logger.error(f"Port {config.port} already in use, is another instance of beeai-server running?")
            return

    # params = [
    #     sys.executable,
    #     "-m",
    #     "uvicorn",
    #     "beeai_server.application:app",
    #     f"--host={host}",
    #     f"--port={config.port}",
    #     "--timeout-keep-alive=2",
    #     "--timeout-graceful-shutdown=2",
    # ]

    # if SSL_KEYFILE is not None and SSL_CERTFILE is not None:
    #     params.append(f"--ssl-keyfile={SSL_KEYFILE}")
    #     params.append(f"--ssl-certfile={SSL_CERTFILE}")

    # os.execv(
    #     sys.executable,
    #     params,
    # )
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "beeai_server.application:app",
            f"--host={host}",
            f"--port={config.port}",
            "--timeout-keep-alive=2",
            "--timeout-graceful-shutdown=2",
        ],
    )


def migrate():
    from beeai_server.infrastructure.persistence.migrations.migrate import migrate as migrate_fn

    migrate_fn()


def create_vector_extension():
    from beeai_server.infrastructure.persistence.migrations.migrate import create_vector_extension as create_fn

    asyncio.run(create_fn())


def create_buckets():
    from beeai_server.infrastructure.object_storage.create_buckets import create_buckets

    configure_logging()
    configuration = get_configuration()
    asyncio.run(create_buckets(configuration.object_storage))


__all__ = ["serve"]
