/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type * as jose from 'jose';

export interface ProviderConfig {
  id: string;
  name: string;
  type: 'oidc';
  issuer: string;
  jwks_url: string;
  client_id: string;
  client_secret: string;
  nextauth_redirect_proxy_url: string;
  JWKS: {
    (protectedHeader?: jose.JWSHeaderParameters, token?: jose.FlattenedJWSInput): Promise<jose.CryptoKey>;
    coolingDown: boolean;
    fresh: boolean;
    reloading: boolean;
    reload: () => Promise<void>;
    jwks: () => jose.JSONWebKeySet | undefined;
  };
}
