/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { extractServiceExtensionDemands, formExtension } from 'beeai-sdk';
import { useMemo } from 'react';

import { getAgentExtensions } from '#api/utils.ts';
import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { AgentDetailPanel } from '#modules/agents/components/AgentDetailPanel.tsx';
import { SourcesPanel } from '#modules/sources/components/SourcesPanel.tsx';

import { useMessages } from '../../messages/contexts/Messages';
import { FormRenderView } from '../components/FormRenderView';
import { RunLandingView } from '../components/RunLandingView';
import { useAgentRun } from '../contexts/agent-run';
import { AgentRunProviders } from '../contexts/agent-run/AgentRunProvider';
import { ChatMessagesView } from './ChatMessagesView';

const formExtensionExtractor = extractServiceExtensionDemands(formExtension);
interface Props {
  agent: Agent;
}

export function ChatView({ agent }: Props) {
  return (
    <AgentRunProviders agent={agent}>
      <Chat />
      <AgentDetailPanel />
    </AgentRunProviders>
  );
}

function Chat() {
  const { isPending, agent } = useAgentRun();
  const { messages } = useMessages();

  // TODO: move extraction into the agent run context (or a2a client)
  const formRender = useMemo(() => {
    const { extensions } = agent.capabilities;
    const formRender = extensions && formExtensionExtractor(getAgentExtensions(agent));

    return formRender ?? undefined;
  }, [agent]);

  const isLanding = !isPending && !messages.length;

  return (
    <>
      <MainContent spacing="md" scrollable={isLanding}>
        {isLanding ? (
          formRender ? (
            <FormRenderView formRender={formRender} />
          ) : (
            <RunLandingView />
          )
        ) : (
          <ChatMessagesView />
        )}
      </MainContent>

      <SourcesPanel />
    </>
  );
}
