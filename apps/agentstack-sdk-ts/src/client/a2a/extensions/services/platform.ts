/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ContextToken } from '../../../context/types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/services/platform_api/v1';

const getMetadata = (contextToken: ContextToken) => {
  return {
    auth_token: contextToken.token,
    expires_at: contextToken.expires_at,
  };
};

export const platformApiExtension = (metadata: Record<string, unknown>, contextToken: ContextToken) => {
  return {
    ...metadata,
    [URI]: getMetadata(contextToken),
  };
};
