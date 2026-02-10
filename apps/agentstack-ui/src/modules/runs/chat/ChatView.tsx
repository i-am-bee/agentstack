/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { SourcesPanel } from '#modules/sources/components/SourcesPanel.tsx';
import { routes } from '#utils/router.ts';

import { FormRenderView } from '../components/FormRenderView';
import { RunLandingView } from '../components/RunLandingView';
import { useAgentRun } from '../contexts/agent-run';
import { AgentRunProviders } from '../contexts/agent-run/AgentRunProvider';
import { useSyncRunStateWithRoute } from '../hooks/useSyncRunStateWithRoute';
import { ChatMessagesView } from './ChatMessagesView';
import classes from './ChatView.module.scss';

interface Props {
  agent: Agent;
}

export function ChatView({ agent }: Props) {
  return (
    <AgentRunProviders agent={agent}>
      <Chat />
    </AgentRunProviders>
  );
}

function Chat() {
  const { isPending, agent, hasMessages, initialFormRender } = useAgentRun();
  const { contextId } = usePlatformContext();

  useSyncRunStateWithRoute();

  const handleMessageSent = () => {
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
  };

  const isLanding = !isPending && !hasMessages;

  return (
    <>
      <MainContent spacing="md" scrollable={isLanding} className={classes.mainContent}>
        {isLanding ? (
          initialFormRender ? (
            <FormRenderView formRender={initialFormRender} onMessageSent={handleMessageSent} />
          ) : (
            <RunLandingView onMessageSent={handleMessageSent} />
          )
        ) : (
          <ChatMessagesView />
        )}
      </MainContent>

      <SourcesPanel />
    </>
  );
}
