/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { IconButton } from '@carbon/react';
import type { MouseEventHandler } from 'react';

import NewSession from './NewSession.svg';
import classes from './NewSessionButton.module.scss';

interface Props {
  onClick: MouseEventHandler;
}

export function NewSessionButton({ onClick }: Props) {
  return (
    <IconButton
      kind="tertiary"
      size="sm"
      label="New session"
      align="bottom"
      autoAlign
      onClick={onClick}
      className={classes.root}
    >
      <NewSession />
    </IconButton>
  );
}
