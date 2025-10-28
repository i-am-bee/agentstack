/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/services/mcp/v1';

const mcpTransportTypesEnum = z.enum(['streamable_http', 'stdio']);
type MCPTransportType = z.infer<typeof mcpTransportTypesEnum>;

const mcpDemandSchema = z.object({
  description: z.string().nullish(),
  suggested: z.array(z.string()).nullish(),
  allowed_transports: z.array(mcpTransportTypesEnum).nullish(),
});

const mcpDemandsSchema = z.object({
  mcp_demands: z.record(z.string(), mcpDemandSchema),
});
export type MCPDemands = z.infer<typeof mcpDemandsSchema>;

const mcpFulfillmentSchema = z.object({
  mcp_fulfillments: z.record(
    z.string(),
    z.object({
      transport: z.object({
        type: mcpTransportTypesEnum,
        url: z.string(),
      }),
    }),
  ),
});
export type MCPFulfillments = z.infer<typeof mcpFulfillmentSchema>;

export const mcpExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof mcpDemandsSchema>,
  {
    mcp_fulfillments: Record<
      string,
      {
        transport: {
          type: MCPTransportType;
          url: string;
        };
      }
    >;
  }
> = {
  getUri: () => URI,
  getDemandsSchema: () => mcpDemandsSchema,
  getFulfillmentSchema: () => mcpFulfillmentSchema,
};
