/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
import { RunView } from '#modules/runs/components/RunView.tsx';

import { ensureModelSelected } from './ensure-model-selected';
import { fetchAgent } from './rsc';

interface Props {
  params: Promise<{ providerId: string }>;
}

export default async function AgentRunPage({ params }: Props) {
  const { providerId } = await params;
  const { featureFlags } = runtimeConfig;

  const agent = await fetchAgent(providerId);

  if (featureFlags.LocalSetup) {
    const { ErrorComponent } = await ensureModelSelected(providerId);
    if (ErrorComponent) {
      return ErrorComponent;
    }
  }

  return (
    <PlatformContextProvider>
      <RunView agent={agent} />
    </PlatformContextProvider>
  );
}
