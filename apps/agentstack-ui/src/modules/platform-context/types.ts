/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListContextsResponse } from './api/types';

enum TitleGenerationState {
  Pending = 'pending',
  Completed = 'completed',
  Failed = 'failed',
}

export enum ModelCapability {
  Llm = 'llm',
  Embedding = 'embedding',
}

export type ContextMetadata = {
  agent_name?: string;
  provider_id?: string;
  title_generation_state?: TitleGenerationState;
  title?: string;
};
export type ContextWithMetadata = ListContextsResponse['items'][number] & { metadata?: ContextMetadata };
