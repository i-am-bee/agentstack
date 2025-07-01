/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';

import { useChat } from '../contexts/chat';
import { ChatProvider } from '../contexts/chat/ChatProvider';
import { useMessages } from '../contexts/messages';
import { MessagesProvider } from '../contexts/messages/MessagesProviders';
import { FileUploadProvider } from '../files/contexts/FileUploadProvider';
import { SourcesPanel } from '../sources/components/SourcesPanel';
import { ChatLandingView } from './ChatLandingView';
import { ChatMessagesView } from './ChatMessagesView';

interface Props {
  agent: Agent;
}

export function ChatView({ agent }: Props) {
  return (
    <FileUploadProvider key={agent.name}>
      <MessagesProvider>
        <ChatProvider agent={agent}>
          <Chat />
        </ChatProvider>
      </MessagesProvider>
    </FileUploadProvider>
  );
}

function Chat() {
  const { isPending } = useChat();
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
