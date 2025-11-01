/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useMemo } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { AgentRunGreeting } from '#modules/agents/components/detail/AgentRunGreeting.tsx';
import { AgentRunHeader } from '#modules/agents/components/detail/AgentRunHeader.tsx';
import { getAgentPromptExamples } from '#modules/agents/utils.ts';
import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { routes } from '#utils/router.ts';

import { FileUpload } from '../../files/components/FileUpload';
import { useAgentRun } from '../contexts/agent-run';
import { SecretsModalPortal } from '../secrets/SecretsModalPortal';
import { RunInput } from './RunInput';
import classes from './RunLandingView.module.scss';

export function RunLandingView() {
  const { agent } = useAgentRun();
  const { messages } = useMessages();
  const { contextId } = usePlatformContext();

  const promptExamples = useMemo(() => getAgentPromptExamples(agent), [agent]);

  const handleMessageSent = useCallback(() => {
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
  }, [agent, contextId, messages]);

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <AgentRunHeader heading={agent.name}>
          <AgentRunGreeting agent={agent} />
        </AgentRunHeader>

        <RunInput promptExamples={promptExamples} onMessageSent={handleMessageSent} />
      </Container>
      <SecretsModalPortal />
    </FileUpload>
  );
}
