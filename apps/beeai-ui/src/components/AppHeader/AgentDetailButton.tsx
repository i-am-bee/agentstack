/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Information } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { useApp } from '#contexts/App/index.ts';

import classes from './AgentDetailButton.module.scss';

export function AgentDetailButton() {
  const { agentDetailOpen, showAgentDetail, hideAgentDetail } = useApp();

  return (
    <IconButton
      kind="tertiary"
      size="sm"
      label="Agent Detail"
      wrapperClasses={classes.root}
      onClick={() => (agentDetailOpen ? hideAgentDetail?.() : showAgentDetail?.())}
    >
      <Information />
    </IconButton>
  );
}
