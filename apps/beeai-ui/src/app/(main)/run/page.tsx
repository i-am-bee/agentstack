/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound } from 'next/navigation';

import { handleApiError } from '#app/(auth)/rsc.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { buildAgent } from '#modules/agents/utils.ts';
import { LIST_CONTEXT_HISTORY_DEFAULT_QUERY } from '#modules/platform-context/api/constants.ts';
import { fetchContextHistory } from '#modules/platform-context/api/index.ts';
import type { ListContextHistoryResponse } from '#modules/platform-context/api/types.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
import { listProviders } from '#modules/providers/api/index.ts';
import { RunView } from '#modules/runs/components/RunView.tsx';

interface Props {
  searchParams: Promise<{ p: string; c?: string }>;
}

export default async function AgentRunPage({ searchParams }: Props) {
  const { p: providerId, c: contextId } = await searchParams;

  let agent: Agent | undefined;
  try {
    const response = await listProviders();

    const provider = response?.items.find(({ id }) => id === providerId);
    if (provider) {
      agent = buildAgent(provider);
    }
  } catch (error) {
    await handleApiError(error);
    console.error('Error fetching agent:', error);
  }

  if (!agent) {
    notFound();
  }

  let initialData: ListContextHistoryResponse | undefined;

  if (contextId) {
    initialData = await fetchContextHistory({
      contextId,
      query: LIST_CONTEXT_HISTORY_DEFAULT_QUERY,
    });

    if (!initialData) {
      notFound();
    }
  }

  return (
    <PlatformContextProvider history={initialData}>
      <RunView agent={agent} />
    </PlatformContextProvider>
  );
}
