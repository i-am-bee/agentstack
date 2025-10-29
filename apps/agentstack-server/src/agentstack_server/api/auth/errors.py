# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


class DiscoveryError(RuntimeError):
    pass


class IssuerDiscoveryError(DiscoveryError):
    pass


class JWKSDiscoveryError(DiscoveryError):
    pass


class IntrospectionDiscoveryError(DiscoveryError):
    pass


class UserInfoDiscoveryError(DiscoveryError):
    pass
