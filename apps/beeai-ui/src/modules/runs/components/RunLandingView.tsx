/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// import { useEffect, useMemo } from 'react';
import { useMemo } from 'react';

import { Container } from '#components/layouts/Container.tsx';
// import { useModal } from '#contexts/Modal/index.tsx';
import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';
import { getAgentPromptExamples } from '#modules/agents/utils.ts';

import { FileUpload } from '../../files/components/FileUpload';
// import { ApiKeysModal } from '../api-keys/ApiKeysModal';
import { useAgentRun } from '../contexts/agent-run';
import { RunInput } from './RunInput';
import classes from './RunLandingView.module.scss';

export function RunLandingView() {
  const { agent } = useAgentRun();

  const promptExamples = useMemo(() => getAgentPromptExamples(agent), [agent]);

  // const { openModal } = useModal();

  // useEffect(() => {
  //   openModal((props) => <ApiKeysModal {...props} />);
  // }, [openModal]);

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <AgentGreeting agent={agent} />

        <RunInput promptExamples={promptExamples} />
      </Container>
    </FileUpload>
  );
}
