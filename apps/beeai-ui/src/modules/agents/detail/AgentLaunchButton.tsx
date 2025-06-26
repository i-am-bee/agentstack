/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from '@carbon/icons-react';
import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';
import isEmpty from 'lodash/isEmpty';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { AddRequiredVariablesModal } from '#modules/variables/components/AddRequiredVariablesModal.tsx';
import { routes } from '#utils/router.ts';

import type { Agent } from '../api/types';
import { useMissingEnvs } from '../hooks/useMissingEnvs';
import { useProviderStatus } from '../hooks/useProviderStatus';
import { isAgentUiSupported } from '../utils';
import classes from './AgentLaunchButton.module.scss';

interface Props {
  agent: Agent;
}

export function AgentLaunchButton({ agent }: Props) {
  const { openModal } = useModal();
  const { provider_id } = agent.metadata;
  const { missingEnvs, isPending: isMissingEnvsPending } = useMissingEnvs({ agent });
  const { isNotInstalled, isStarting, isError } = useProviderStatus({ providerId: provider_id });
  const isUiSupported = isAgentUiSupported(agent);

  if (isNotInstalled || isStarting || isError || !isUiSupported) {
    return null;
  }

  return (
    <Button
      kind="primary"
      size="md"
      className={classes.button}
      renderIcon={ArrowRight}
      disabled={isMissingEnvsPending}
      {...(isEmpty(missingEnvs)
        ? {
            as: TransitionLink,
            href: routes.agentRun({ name: agent.name }),
          }
        : {
            onClick: () => {
              openModal((props) => <AddRequiredVariablesModal {...props} missingEnvs={missingEnvs} />);
            },
          })}
    >
      Launch this agent
    </Button>
  );
}

AgentLaunchButton.Skeleton = function AgentLaunchButtonSkeleton() {
  /* .cds--layout--size-md fixes Carbon bug where button size prop is not respected */
  return <ButtonSkeleton size="md" className={clsx('cds--layout--size-md', classes.root)} />;
};
