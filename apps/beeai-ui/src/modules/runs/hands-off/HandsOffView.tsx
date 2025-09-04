/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { formExtension } from '#api/a2a/extensions/ui/form.ts';
import { extractServiceExtensionDemands } from '#api/a2a/extensions/utils.ts';
import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import { SourcesPanel } from '#modules/sources/components/SourcesPanel.tsx';

import { FormRenderView } from '../components/FormRenderView';
import { RunLandingView } from '../components/RunLandingView';
import { useAgentRun } from '../contexts/agent-run';
import { AgentRunProviders } from '../contexts/agent-run/AgentRunProvider';
import { HandsOffOutputView } from './HandsOffOutputView';

const formExtensionExtractor = extractServiceExtensionDemands(formExtension);

interface Props {
  agent: Agent;
}

export function HandsOffView({ agent }: Props) {
  return (
    <AgentRunProviders agent={agent}>
      <HandsOff />
    </AgentRunProviders>
  );
}

function HandsOff() {
  const { agent, isPending } = useAgentRun();

  const formRender = useMemo(() => {
    const { extensions } = agent.capabilities;
    const formRender = extensions && formExtensionExtractor(extensions);

    return formRender ?? undefined;
  }, [agent.capabilities]);

  const { messages } = useMessages();

  const isIdle = !(isPending || messages?.length);

  return (
    <>
      <MainContent spacing="md">
        {isIdle ? formRender ? <FormRenderView formRender={formRender} /> : <RunLandingView /> : <HandsOffOutputView />}
      </MainContent>

      <SourcesPanel />
    </>
  );
}
