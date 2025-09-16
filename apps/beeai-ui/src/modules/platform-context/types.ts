/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiQuery } from '#@types/utils.ts';

export enum ModelCapability {
  LLM = 'llm',
  EMBEDDING = 'embedding',
}

type ListContextsQery = ApiQuery<'/api/v1/contexts'>;

type ListContextHistoryQuery = ApiQuery<'/api/v1/contexts/{context_id}/history'>;

export type ListContextsParams = {
  query?: ListContextsQery;
};

export type ListContextHistoryParams = {
  contextId: string;
  query?: ListContextHistoryQuery;
};
