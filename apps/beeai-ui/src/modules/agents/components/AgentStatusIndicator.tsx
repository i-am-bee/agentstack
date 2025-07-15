/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { InlineLoading } from '@carbon/react';

import type { Agent } from '../api/types';
import { useProviderStatus } from '../hooks/useProviderStatus';
import classes from './AgentStatusIndicator.module.scss';

interface Props {
  agent: Agent;
}

export function AgentStatusIndicator({ agent }: Props) {
  const { isStarting } = useProviderStatus({ providerId: agent.provider.id });

  if (isStarting) {
    return (
      <div className={classes.root}>
        <InlineLoading />
      </div>
    );
  }
  return null;
}
