/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ContextToken } from '../../../../api/contexts/types';

export const PLATFORM_API_EXTENSION_URI = 'https://a2a-extensions.agentstack.beeai.dev/services/platform_api/v1';

export const platformApiExtension = (metadata: Record<string, unknown>, contextToken: ContextToken) => {
  return {
    ...metadata,
    [PLATFORM_API_EXTENSION_URI]: {
      auth_token: contextToken.token,
      expires_at: contextToken.expires_at,
    },
  };
};
