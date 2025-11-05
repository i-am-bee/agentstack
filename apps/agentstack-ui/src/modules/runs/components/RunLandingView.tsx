/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useMemo } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { AgentRunGreeting } from '#modules/agents/components/detail/AgentRunGreeting.tsx';
import { AgentRunHeader } from '#modules/agents/components/detail/AgentRunHeader.tsx';
import { getAgentPromptExamples } from '#modules/agents/utils.ts';

import { FileUpload } from '../../files/components/FileUpload';
import { useAgentRun } from '../contexts/agent-run';
import { useAgentSecrets } from '../contexts/agent-secrets';
import { ProvideSecretsWarning } from '../secrets/ProvideSecretsWarning';
import { RunInput } from './RunInput';
import classes from './RunLandingView.module.scss';

interface Props {
  onMessageSent?: () => void;
}

export function RunLandingView({ onMessageSent }: Props) {
  const { agent } = useAgentRun();
  const { demandedSecrets } = useAgentSecrets();

  const unresolvedSecrets = useMemo(() => demandedSecrets.filter(({ isReady }) => !isReady), [demandedSecrets]);
  const hasUnresolvedSecrets = unresolvedSecrets.length > 0;

  const promptExamples = useMemo(() => getAgentPromptExamples(agent), [agent]);

  return (
    <FileUpload>
      <Container size="sm" className={clsx(classes.root, { [classes.hasSecretsWarning]: hasUnresolvedSecrets })}>
        {hasUnresolvedSecrets && <ProvideSecretsWarning />}

        <div className={classes.content}>
          <AgentRunHeader heading={agent.name}>
            <AgentRunGreeting agent={agent} />
          </AgentRunHeader>

          <RunInput promptExamples={promptExamples} onMessageSent={onMessageSent} />
        </div>
      </Container>
    </FileUpload>
  );
}
