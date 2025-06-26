/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Agent } from '@i-am-bee/beeai-ui';

import { fetchAgentMetadata } from '@/utils/fetchAgentMetadata';
import { fetchAgentRegistry } from '@/utils/fetchAgentRegistry';

export async function fetchAgentsList() {
  const registry = await fetchAgentRegistry();
  const { providers } = registry;
  const agents = (
    await Promise.all(providers.map(async ({ location }) => await fetchAgentMetadata({ dockerImageId: location })))
  ).flatMap(({ agents }) => agents);

  return agents as Agent[];
}
