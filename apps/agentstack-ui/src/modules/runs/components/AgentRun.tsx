/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound } from 'next/navigation';

import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { LIST_CONTEXT_HISTORY_DEFAULT_QUERY } from '#modules/platform-context/api/constants.ts';
import { fetchContextHistory } from '#modules/platform-context/api/index.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
import { RunView } from '#modules/runs/components/RunView.tsx';

import { ensureModelSelected } from '../../../app/(main)/agent/[providerId]/ensure-model-selected';
import { fetchAgent } from '../../../app/(main)/agent/[providerId]/rsc';

interface Props {
  providerId: string;
  contextId?: string;
}

export async function AgentRun({ providerId, contextId }: Props) {
  const { featureFlags } = runtimeConfig;

  const agentPromise = fetchAgent(providerId);
  const contextHistoryPromise = contextId
    ? fetchContextHistory({
        context_id: contextId,
        query: LIST_CONTEXT_HISTORY_DEFAULT_QUERY,
      })
    : undefined;

  const agent = await agentPromise;

  if (featureFlags.LocalSetup) {
    const { ErrorComponent } = await ensureModelSelected(agent);

    if (ErrorComponent) {
      return ErrorComponent;
    }
  }

  const contextHistory = await contextHistoryPromise;

  if (contextId && !contextHistory) {
    notFound();
  }

  return (
    <PlatformContextProvider contextId={contextId} history={contextHistory}>
      <RunView agent={agent} />
    </PlatformContextProvider>
  );
}
