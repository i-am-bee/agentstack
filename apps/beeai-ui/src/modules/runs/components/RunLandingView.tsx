/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';
import { getAgentPromptExamples } from '#modules/agents/utils.ts';

import { FileUpload } from '../../files/components/FileUpload';
import { useAgentRun } from '../contexts/agent-run';
import { SecretsModalPortal } from '../secrets/SecretsModalPortal';
import { RunInput } from './RunInput';
import classes from './RunLandingView.module.scss';

export function RunLandingView() {
  const { agent } = useAgentRun();

  const promptExamples = useMemo(() => getAgentPromptExamples(agent), [agent]);

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <AgentGreeting agent={agent} />

        <RunInput promptExamples={promptExamples} />
      </Container>
      <SecretsModalPortal />
    </FileUpload>
  );
}
