/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension } from '../../../../core/extensions/types';
import { mcpDemandsSchema, mcpFulfillmentsSchema } from './schemas';
import type { MCPDemands, MCPFulfillments } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/services/mcp/v1';

export const mcpExtension: A2AServiceExtension<typeof URI, MCPDemands, MCPFulfillments> = {
  getUri: () => URI,
  getDemandsSchema: () => mcpDemandsSchema,
  getFulfillmentsSchema: () => mcpFulfillmentsSchema,
};
