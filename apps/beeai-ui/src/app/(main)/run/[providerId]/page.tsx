/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { handleApiError } from '#app/(auth)/rsc.tsx';
import { ErrorPage } from '#components/ErrorPage/ErrorPage.tsx';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { readConfigurationsSystem } from '#modules/configurations/api/index.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
import { NoModelSelectedErrorPage } from '#modules/runs/components/NoModelSelectedErrorPage.tsx';
import { RunView } from '#modules/runs/components/RunView.tsx';

import { fetchAgent } from './rsc';

interface Props {
  params: Promise<{ providerId: string }>;
}

export default async function AgentRunPage({ params }: Props) {
  const { providerId } = await params;

  if (runtimeConfig.featureFlags.LocalSetup) {
    try {
      const config = await readConfigurationsSystem();
      if (!config?.default_llm_model) {
        return <NoModelSelectedErrorPage />;
      }
    } catch (error) {
      await handleApiError(error);
      return <ErrorPage message="There was an error loading system configuration." />;
    }
  }

  const agent = await fetchAgent(providerId);

  return (
    <PlatformContextProvider>
      <RunView agent={agent} />
    </PlatformContextProvider>
  );
}
