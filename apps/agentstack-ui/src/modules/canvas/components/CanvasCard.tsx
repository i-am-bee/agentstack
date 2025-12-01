/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { License } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEventHandler } from 'react';

import classes from './CanvasCard.module.scss';

interface Props {
  heading?: string;
  className?: string;
  isActive?: boolean;
  onClick: MouseEventHandler;
}

export function CanvasCard({ heading, className, isActive, onClick }: Props) {
  return (
    <Button className={clsx(classes.root, className, { [classes.active]: isActive })} onClick={onClick}>
      <span className={classes.icon}>
        <License />
      </span>

      <span className={classes.heading}>{heading ?? <span className={classes.untitled}>Untitled</span>}</span>
    </Button>
  );
}
