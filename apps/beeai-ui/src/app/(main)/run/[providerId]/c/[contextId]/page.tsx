/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound } from 'next/navigation';

import { LIST_CONTEXT_HISTORY_DEFAULT_QUERY } from '#modules/platform-context/api/constants.ts';
import { fetchContextHistory } from '#modules/platform-context/api/index.ts';
import type { ListContextHistoryResponse } from '#modules/platform-context/api/types.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
import { RunView } from '#modules/runs/components/RunView.tsx';

import { fetchAgent } from '../../rsc';

interface Props {
  params: Promise<{ providerId: string; contextId: string }>;
}

export default async function AgentRunPage({ params }: Props) {
  const { providerId, contextId } = await params;

  const agent = await fetchAgent(providerId);

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
    <PlatformContextProvider history={initialData} contextId={contextId}>
      <RunView agent={agent} />
    </PlatformContextProvider>
  );
}
