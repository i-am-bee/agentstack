/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { MessageFormProvider } from '#modules/form/contexts/MessageFormProvider.tsx';
import { MessageFormResponse } from '#modules/messages/components/MessageFormResponse.tsx';
import { checkMessageContent, isAgentMessage, isUserMessage } from '#modules/messages/utils.ts';
import { routes } from '#utils/router.ts';

import { useMessages } from '../../messages/contexts/Messages';
import { MessageTrajectories } from '../../trajectories/components/MessageTrajectories';
import { NewSessionButton } from '../components/NewSessionButton';
import { useAgentRun } from '../contexts/agent-run';
import classes from './HandsOffOutputView.module.scss';
import { HandsOffText } from './HandsOffText';
import { TaskStatusBar } from './TaskStatusBar';

export function HandsOffOutputView() {
  const { agent, input, isPending, cancel } = useAgentRun();
  const { messages } = useMessages();
  const [showSubmission, setShowSubmission] = useState(false);

  const router = useRouter();

  const form = messages.find(isUserMessage)?.form;
  const message = messages.find(isAgentMessage);
  const hasOutput = message ? checkMessageContent(message) : false;
  const containerSize = hasOutput ? 'md' : 'sm';

  return (
    <div className={classes.root}>
      <Container size={containerSize} className={classes.holder}>
        <header className={classes.header}>
          <div className={classes.headerContainer}>
            {(form || input) && (
              <div className={classes.input}>
                {form ? (
                  <MessageFormProvider showSubmission={showSubmission} setShowSubmission={setShowSubmission}>
                    <MessageFormResponse form={form} />
                  </MessageFormProvider>
                ) : (
                  <p>{input}</p>
                )}
              </div>
            )}

            <NewSessionButton
              onClick={() => {
                router.push(routes.agentRun({ providerId: agent.provider.id }));
              }}
            />
          </div>
        </header>

        <div className={classes.body}>
          {message && (
            <>
              <HandsOffText message={message} className={classes.text} />

              <MessageTrajectories message={message} isPending={isPending} />
            </>
          )}

          {isPending && (
            <div className={classes.statusBar}>
              <TaskStatusBar onStopClick={cancel} />
            </div>
          )}
        </div>
      </Container>
    </div>
  );
}
