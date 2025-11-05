/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { extractServiceExtensionDemands, formExtension } from 'agentstack-sdk';
import { useCallback, useMemo } from 'react';

import { getAgentExtensions } from '#api/utils.ts';
import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { AgentDetailPanel } from '#modules/agents/components/detail/AgentDetailPanel.tsx';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { SourcesPanel } from '#modules/sources/components/SourcesPanel.tsx';
import { routes } from '#utils/router.ts';

import { FormRenderView } from '../components/FormRenderView';
import { RunLandingView } from '../components/RunLandingView';
import { useAgentRun } from '../contexts/agent-run';
import { AgentRunProviders } from '../contexts/agent-run/AgentRunProvider';
import { useSyncRunStateWithRoute } from '../hooks/useSyncRunStateWithRoute';
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
  const { isPending, hasMessages } = useAgentRun();

  useSyncRunStateWithRoute();

  const isLanding = !isPending && !hasMessages;

  return (
    <>
      <MainContent spacing="md" scrollable={isLanding}>
        {isLanding ? <LandingView /> : <ChatMessagesView />}
      </MainContent>

      <SourcesPanel />
    </>
  );
}

function LandingView() {
  const { agent } = useAgentRun();
  const { contextId } = usePlatformContext();

  const handleMessageSent = useCallback(() => {
    if (contextId) {
      window.history.pushState(
        null,
        '',
        routes.agentRun({
          providerId: agent.provider.id,
          contextId,
        }),
      );
    }
  }, [agent, contextId]);

  // TODO: move extraction into the agent run context (or a2a client)
  const formRender = useMemo(() => {
    const agentExtensions = getAgentExtensions(agent);
    const formRender = formExtensionExtractor(agentExtensions);

    return formRender ?? undefined;
  }, [agent]);

  if (formRender) {
    return <FormRenderView formRender={formRender} onMessageSent={handleMessageSent} />;
  }

  return <RunLandingView onMessageSent={handleMessageSent} />;
}
