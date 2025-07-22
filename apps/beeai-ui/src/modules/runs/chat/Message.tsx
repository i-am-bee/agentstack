/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import type { UIMessage } from '#modules/messages/types.ts';
import { UIMessageStatus } from '#modules/messages/types.ts';
import {
  checkMessageError,
  getMessageContent,
  getMessageSources,
  isAgentMessage,
  isUserMessage,
} from '#modules/messages/utils.ts';
import { MessageSources } from '#modules/sources/components/MessageSources.tsx';

import { MessageFiles } from '../../files/components/MessageFiles';
import { MessageTrajectories } from '../../trajectories/components/MessageTrajectories';
import { AgentIcon } from '../components/AgentIcon';
import { MessageContent } from '../components/MessageContent';
import { MessageError } from '../components/MessageError';
import { useAgentRun } from '../contexts/agent-run';
import classes from './Message.module.scss';
import { UserIcon } from './UserIcon';

interface Props {
  message: UIMessage;
}

export function Message({ message }: Props) {
  const { agent } = useAgentRun();

  const content = getMessageContent(message);
  const sources = getMessageSources(message);

  const isUser = isUserMessage(message);
  const isAgent = isAgentMessage(message);
  const isPending = isAgent && message.status === UIMessageStatus.InProgress && !content;
  const isError = isAgent && checkMessageError(message);

  return (
    <li className={clsx(classes.root)}>
      <div className={classes.sender}>
        <div className={classes.senderIcon}>{isUser ? <UserIcon /> : <AgentIcon />}</div>
        <div className={classes.senderName}>{isUser ? 'User' : agent.ui.display_name}</div>
      </div>

      <div className={classes.body}>
        {isPending ? (
          <Spinner />
        ) : (
          <>
            <div className={clsx(classes.content, { [classes.isUser]: isUser })}>
              <MessageContent content={content} sources={sources} />
            </div>

            {isError && <MessageError message={message} />}
          </>
        )}

        <MessageFiles message={message} className={classes.files} />

        {isAgent && <MessageSources message={message} />}

        {isAgent && <MessageTrajectories message={message} />}
      </div>
    </li>
  );
}
