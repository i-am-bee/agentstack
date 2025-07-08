/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';

import { useAgentRun } from '../contexts/agent-run';
import { AgentRunProvider } from '../contexts/agent-run/AgentRunProvider';
import { useMessages } from '../contexts/messages';
import { FileUploadProvider } from '../files/contexts/FileUploadProvider';
import { SourcesPanel } from '../sources/components/SourcesPanel';
import { ChatLandingView } from './ChatLandingView';
import { ChatMessagesView } from './ChatMessagesView';

interface Props {
  agent: Agent;
}

export function ChatView({ agent }: Props) {
  return (
    <FileUploadProvider allowedContentTypes={agent.input_content_types ?? []}>
      <AgentRunProvider agent={agent}>
        <Chat />
      </AgentRunProvider>
    </FileUploadProvider>
  );
}

function Chat() {
  const { isPending } = useAgentRun();
  const { messages } = useMessages();

  const isIdle = !(isPending || messages.length);

  return (
    <>
      <MainContent spacing="md" scrollable={isIdle}>
        {isIdle ? <ChatLandingView /> : <ChatMessagesView />}
      </MainContent>

      <SourcesPanel />
    </>
  );
}
