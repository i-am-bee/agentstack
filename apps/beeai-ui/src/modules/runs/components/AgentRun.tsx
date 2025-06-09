/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { Loading } from '@carbon/react';

import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { type Agent, UiType } from '#modules/agents/api/types.ts';

import { useAgent } from '../../agents/api/queries/useAgent';
import { Chat } from '../chat/Chat';
import { ChatProvider } from '../contexts/chat/ChatProvider';
import { HandsOffProvider } from '../contexts/hands-off/HandsOffProvider';
import { FileUploadProvider } from '../files/contexts/FileUploadProvider';
import { HandsOff } from '../hands-off/HandsOff';
import classes from './AgentRun.module.scss';

interface Props {
  name: string;
}

export function AgentRun({ name }: Props) {
  const { data: agent, isPending, refetch, isRefetching, error } = useAgent({ name });

  return !isPending ? (
    agent ? (
      renderUi({ agent })
    ) : (
      <MainContent>
        <Container size="sm">
          <ErrorMessage
            title="Failed to load the agent."
            onRetry={refetch}
            isRefetching={isRefetching}
            subtitle={error?.message}
          />
        </Container>
      </MainContent>
    )
  ) : (
    <MainContent>
      <div className={classes.loading}>
        <Loading withOverlay={false} />
      </div>
    </MainContent>
  );
}

const renderUi = ({ agent }: { agent: Agent }) => {
  const type = agent.metadata.ui?.type;

  switch (type) {
    case UiType.Chat:
      return (
        <FileUploadProvider>
          <MainContent limitHeight>
            <ChatProvider agent={agent}>
              <Chat />
            </ChatProvider>
          </MainContent>
        </FileUploadProvider>
      );
    case UiType.HandsOff:
      return (
        <FileUploadProvider>
          <HandsOffProvider agent={agent}>
            <HandsOff />
          </HandsOffProvider>
        </FileUploadProvider>
      );
    default:
      return (
        <MainContent>
          <Container size="sm">
            <h1>{agent.name}</h1>
            <div className={classes.uiNotAvailable}>
              {type
                ? `The UI requested by the agent is not available: '${type}'`
                : `The agent doesn’t have a defined UI.`}
            </div>
          </Container>
        </MainContent>
      );
  }
};
