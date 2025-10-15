/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { extractServiceExtensionDemands, formExtension } from 'beeai-sdk';
import { useMemo } from 'react';

import { getAgentExtensions } from '#api/utils.ts';
import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { AgentDetailPanel } from '#modules/agents/components/detail/AgentDetailPanel.tsx';
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
      <AgentDetailPanel />
    </AgentRunProviders>
  );
}

function HandsOff() {
  const { agent, isPending } = useAgentRun();

  // TODO: move extraction into the agent run context (or a2a client)
  const formRender = useMemo(() => {
    const agentExtensions = getAgentExtensions(agent);
    const formRender = formExtensionExtractor(agentExtensions);

    return formRender ?? undefined;
  }, [agent]);

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
