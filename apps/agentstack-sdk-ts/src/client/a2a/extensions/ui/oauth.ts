/**
 * Copyright 2025 © Agent Stack a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.dev/auth/oauth/v1';

const schema = z.object({
  authorization_endpoint_url: z.string(),
});

export type OAuthRequest = z.infer<typeof schema>;

export const oauthRequestExtension: A2AUiExtension<typeof URI, OAuthRequest> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};
