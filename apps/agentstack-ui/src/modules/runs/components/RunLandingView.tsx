/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { AgentRunGreeting } from '#modules/agents/components/detail/AgentRunGreeting.tsx';
import { AgentRunHeader } from '#modules/agents/components/detail/AgentRunHeader.tsx';
import { getAgentPromptExamples } from '#modules/agents/utils.ts';

import { FileUpload } from '../../files/components/FileUpload';
import { useAgentRun } from '../contexts/agent-run';
import { SecretsModalPortal } from '../secrets/SecretsModalPortal';
import { RunInput } from './RunInput';
import classes from './RunLandingView.module.scss';

interface Props {
  onMessageSent?: () => void;
}

export function RunLandingView({ onMessageSent }: Props) {
  const { agent } = useAgentRun();

  const promptExamples = useMemo(() => getAgentPromptExamples(agent), [agent]);

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <AgentRunHeader heading={agent.name}>
          <AgentRunGreeting agent={agent} />
        </AgentRunHeader>

        <RunInput promptExamples={promptExamples} onMessageSent={onMessageSent} />
      </Container>
      <SecretsModalPortal />
    </FileUpload>
  );
}
