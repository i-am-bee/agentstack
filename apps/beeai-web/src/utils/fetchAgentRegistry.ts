/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { parse } from 'yaml';

import { AGENT_REGISTRY_URL } from '@/constants';

import { ensureResponse } from './ensureResponse';

type AgentRegistry = { providers: { location: string }[] };

export async function fetchAgentRegistry(): Promise<AgentRegistry> {
  const response = await fetch(AGENT_REGISTRY_URL);
  const registry = await ensureResponse<string>({
    response,
    errorContext: 'agent registry',
    resolveAs: 'text',
  });

  return parse(registry);
}
