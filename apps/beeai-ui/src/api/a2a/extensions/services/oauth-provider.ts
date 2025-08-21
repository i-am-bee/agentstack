/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/auth/oauth/v1';

const oauthDemandSchema = z.object({
  redirect_uri: z.boolean(),
});

export const demandsSchema = z.object({
  oauth_demands: z.record(z.string(), oauthDemandSchema),
});
export type OAuthDemand = z.infer<typeof demandsSchema>;

const fulfillmentSchema = z.object({
  oauth_fulfillments: z.record(
    z.string(),
    z.object({
      redirect_uri: z.string(),
    }),
  ),
});
export type OAuthFulfillment = z.infer<typeof fulfillmentSchema>;

export const oauthProviderExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof demandsSchema>,
  {
    oauth_fulfillments: Record<
      string,
      {
        redirect_uri: string;
      }
    >;
  }
> = {
  getUri: () => URI,
  getDemandsSchema: () => demandsSchema,
  getFulfillmentSchema: () => fulfillmentSchema,
};
