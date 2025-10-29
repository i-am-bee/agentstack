/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.dev/auth/oauth/v1';

const oauthDemandSchema = z.object({
  redirect_uri: z.boolean(),
});

const oauthDemandsSchema = z.object({
  oauth_demands: z.record(z.string(), oauthDemandSchema),
});
export type OAuthDemands = z.infer<typeof oauthDemandsSchema>;

const oauthFulfillmentSchema = z.object({
  oauth_fulfillments: z.record(
    z.string(),
    z.object({
      redirect_uri: z.string(),
    }),
  ),
});
export type OAuthFulfillments = z.infer<typeof oauthFulfillmentSchema>;

export const oauthProviderExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof oauthDemandsSchema>,
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
  getDemandsSchema: () => oauthDemandsSchema,
  getFulfillmentSchema: () => oauthFulfillmentSchema,
};

export const oauthMessageSchema = z.object({
  data: z.object({
    redirect_uri: z.string(),
  }),
});
