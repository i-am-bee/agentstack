/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { AgentIcon } from '#modules/runs/components/AgentIcon.tsx';

import { type Agent, SupportedUIType } from '../api/types';
import classes from './AgentHeading.module.scss';

interface Props {
  agent: Agent;
}

export function AgentHeading({ agent }: Props) {
  const {
    name,
    ui: { ui_type },
  } = agent;

  const isChatUi = ui_type === SupportedUIType.Chat;
  const isHandsOffUi = ui_type === SupportedUIType.HandsOff;

  return (
    <h1 className={clsx(classes.root, { [classes[`ui--${ui_type}`]]: ui_type })}>
      <AgentIcon size={isChatUi ? 'xl' : undefined} inverted={isHandsOffUi} />

      <span className={classes.name}>{name}</span>
    </h1>
  );
}
