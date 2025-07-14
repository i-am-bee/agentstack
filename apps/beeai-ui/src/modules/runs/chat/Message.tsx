/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { Spinner } from '#components/Spinner/Spinner.tsx';

import { AgentIcon } from '../components/AgentIcon';
import { MessageContent } from '../components/MessageContent';
import { MessageError } from '../components/MessageError';
import { useAgentRun } from '../contexts/agent-run';
import { MessageFiles } from '../files/components/MessageFiles';
import { MessageSources } from '../sources/components/MessageSources';
import { MessageTrajectories } from '../trajectory/components/MessageTrajectories';
import { isAgentMessage, isUserMessage } from '../utils';
import classes from './Message.module.scss';
import { type ChatMessage, MessageStatus } from './types';
import { UserIcon } from './UserIcon';

interface Props {
  message: ChatMessage;
}

export function Message({ message }: Props) {
  const { agent } = useAgentRun();
  const { content } = message;

  const isUser = isUserMessage(message);
  const isAgent = isAgentMessage(message);
  const isPending = isAgent && message.status === MessageStatus.InProgress && !content;
  const isError = isAgent && (message.status === MessageStatus.Failed || message.status === MessageStatus.Aborted);

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
              <MessageContent message={message} />
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
