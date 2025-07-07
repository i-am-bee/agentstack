/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { type Agent, UiType } from '#modules/agents/api/types.ts';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';

import { Chat } from '../chat/Chat';
import { ChatProvider } from '../contexts/chat/ChatProvider';
import { HandsOffProvider } from '../contexts/hands-off/HandsOffProvider';
import { FileUploadProvider } from '../files/contexts/FileUploadProvider';
import { HandsOff } from '../hands-off/HandsOff';
import classes from './AgentRun.module.scss';

interface Props {
  agent: Agent;
}

export function AgentRun({ agent }: Props) {
  const { ui_type, display_name } = getAgentUiMetadata(agent);

  switch (ui_type) {
    case UiType.Chat:
      return (
        <FileUploadProvider key={agent.name}>
          <ChatProvider agent={agent}>
            <Chat />
          </ChatProvider>
        </FileUploadProvider>
      );
    case UiType.HandsOff:
      return (
        <FileUploadProvider key={agent.name}>
          <HandsOffProvider agent={agent}>
            <HandsOff />
          </HandsOffProvider>
        </FileUploadProvider>
      );
    default:
      return (
        <MainContent>
          <Container size="sm">
            <h1>{display_name}</h1>
            <div className={classes.uiNotAvailable}>
              {ui_type
                ? `The UI requested by the agent is not available: '${ui_type}'`
                : 'The agent doesn’t have a defined UI.'}
            </div>
          </Container>
        </MainContent>
      );
  }
}
