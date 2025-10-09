/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AUiExtension } from 'beeai-sdk';
import { z } from 'zod';

const URI = 'https://a2a-extensions.beeai.dev/auth/oauth/v1';

const schema = z.object({
  authorization_endpoint_url: z.string(),
});

export type OAuthRequest = z.infer<typeof schema>;

export const oauthRequestExtension: A2AUiExtension<typeof URI, OAuthRequest> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};
