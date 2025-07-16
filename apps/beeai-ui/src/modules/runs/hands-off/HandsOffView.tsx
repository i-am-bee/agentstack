/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';

import { useAgentRun } from '../contexts/agent-run';
import { AgentRunProviders } from '../contexts/agent-run/AgentRunProvider';
import { useMessages } from '../contexts/messages';
import { SourcesPanel } from '../sources/components/SourcesPanel';
import { HandsOffLandingView } from './HandsOffLandingView';
import { HandsOffOutputView } from './HandsOffOutputView';

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
  const { isPending } = useAgentRun();
  const { messages } = useMessages();

  const isIdle = !(isPending || messages?.length);

  return (
    <>
      <MainContent spacing="md">{isIdle ? <HandsOffLandingView /> : <HandsOffOutputView />}</MainContent>

      <SourcesPanel />
    </>
  );
}
