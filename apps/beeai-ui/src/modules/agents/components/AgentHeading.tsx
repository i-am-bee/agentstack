/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { AgentIcon } from '#modules/runs/components/AgentIcon.tsx';

import { type Agent, InteractionMode } from '../api/types';
import classes from './AgentHeading.module.scss';

interface Props {
  agent: Agent;
}

export function AgentHeading({ agent }: Props) {
  const {
    name,
    ui: { interaction_mode },
  } = agent;

  const isChatUi = interaction_mode === InteractionMode.MultiTurn;
  const isHandsOffUi = interaction_mode === InteractionMode.SingleTurn;

  return (
    <h1 className={clsx(classes.root, { [classes[`ui--${interaction_mode}`]]: interaction_mode })}>
      <AgentIcon size={isChatUi ? 'xl' : undefined} inverted={isHandsOffUi} />

      <span className={classes.name}>{name}</span>
    </h1>
  );
}
