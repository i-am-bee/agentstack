/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useMemo } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';
import { AgentHeader } from '#modules/agents/components/AgentHeader.tsx';
import { AgentName } from '#modules/agents/components/AgentName.tsx';
import { getAgentPromptExamples } from '#modules/agents/utils.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { routes } from '#utils/router.ts';

import { FileUpload } from '../../files/components/FileUpload';
import { useAgentRun } from '../contexts/agent-run';
import { SecretsModalPortal } from '../secrets/SecretsModalPortal';
import { RunInput } from './RunInput';
import classes from './RunLandingView.module.scss';

export function RunLandingView() {
  const { agent } = useAgentRun();
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
  }, [agent.provider.id, contextId]);

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <AgentHeader>
          <AgentName>{agent.name}</AgentName>

          <AgentGreeting agent={agent} />
        </AgentHeader>

        <RunInput promptExamples={promptExamples} onMessageSent={handleMessageSent} />
      </Container>
      <SecretsModalPortal />
    </FileUpload>
  );
}
