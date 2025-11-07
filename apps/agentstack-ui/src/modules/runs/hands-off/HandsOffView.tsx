/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

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
  const { isPending, initialFormRender } = useAgentRun();
  const { messages } = useMessages();

  const isIdle = !(isPending || messages?.length);

  return (
    <>
      <MainContent spacing="md">
        {isIdle ? (
          initialFormRender ? (
            <FormRenderView formRender={initialFormRender} />
          ) : (
            <RunLandingView />
          )
        ) : (
          <HandsOffOutputView />
        )}
      </MainContent>

      <SourcesPanel />
    </>
  );
}
