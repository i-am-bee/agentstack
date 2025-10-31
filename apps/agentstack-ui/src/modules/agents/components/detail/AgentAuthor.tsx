/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentDetailContributor } from 'agentstack-sdk';

import { getNameInitials } from '#utils/helpers.ts';

import classes from './AgentAuthor.module.scss';

interface Props {
  author: AgentDetailContributor;
}

export function AgentAuthor({ author }: Props) {
  const { name } = author;
  const initials = getNameInitials(name);

  return (
    <p className={classes.root}>
      {initials && <span className={classes.initials}>{initials}</span>}

      <span className={classes.name}>{name}</span>
    </p>
  );
}
