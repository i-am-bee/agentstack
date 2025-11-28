/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { OIDCConfig } from 'next-auth/providers';

import type { ProviderConfig } from '../types';

export function Auth0Provider(config: ProviderConfig, audience: string): OIDCConfig<unknown> {
  return {
    id: config.id,
    name: 'auth0',
    type: 'oidc',
    idToken: true,
    style: { text: '#ffffff', bg: '#252525' },
    options: {
      issuer: config.issuer,
      clientId: config.client_id,
      clientSecret: config.client_secret,
      authorization: {
        params: {
          audience,
        },
      },
    },
  };
}
