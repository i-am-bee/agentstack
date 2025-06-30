/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEventHandler } from 'react';

import classes from './TrajectoryButton.module.scss';

interface Props {
  isOpen?: boolean;
  onClick?: MouseEventHandler;
}

export function TrajectoryButton({ isOpen, onClick }: Props) {
  return (
    <Button
      kind="ghost"
      size="sm"
      renderIcon={ChevronDown}
      className={clsx(classes.root, { [classes.isOpen]: isOpen })}
      onClick={onClick}
    >
      How did I get this answer?
    </Button>
  );
}
