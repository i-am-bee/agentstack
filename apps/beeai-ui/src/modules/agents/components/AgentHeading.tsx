/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { AgentIcon } from '#modules/runs/components/AgentIcon.tsx';

import { type Agent, UiType } from '../api/types';
import { getAgentUiMetadata } from '../utils';
import classes from './AgentHeading.module.scss';

interface Props {
  agent: Agent;
}

export function AgentHeading({ agent }: Props) {
  const { display_name, ui_type } = getAgentUiMetadata(agent);

  const isChatUi = ui_type === UiType.Chat;
  const isHandsOffUi = ui_type === UiType.HandsOff;

  return (
    <h1 className={clsx(classes.root, { [classes[`ui--${ui_type}`]]: ui_type })}>
      <AgentIcon size={isChatUi ? 'xl' : undefined} inverted={isHandsOffUi} />

      <span className={classes.name}>{display_name}</span>
    </h1>
  );
}
