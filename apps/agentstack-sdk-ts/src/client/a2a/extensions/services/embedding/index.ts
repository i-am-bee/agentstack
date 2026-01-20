/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension } from '../../../../core/extensions/types';
import { embeddingDemandsSchema, embeddingFulfillmentsSchema } from './schemas';
import type { EmbeddingDemands, EmbeddingFulfillments } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/services/embedding/v1';

export const embeddingExtension: A2AServiceExtension<typeof URI, EmbeddingDemands, EmbeddingFulfillments> = {
  getUri: () => URI,
  getDemandsSchema: () => embeddingDemandsSchema,
  getFulfillmentsSchema: () => embeddingFulfillmentsSchema,
};
