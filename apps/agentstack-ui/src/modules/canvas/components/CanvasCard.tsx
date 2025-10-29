/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { License } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEventHandler } from 'react';

import classes from './CanvasCard.module.scss';

interface Props {
  heading: string;
  className?: string;
  onClick: MouseEventHandler;
}

export function CanvasCard({ heading, className, onClick }: Props) {
  return (
    <div className={clsx(classes.root, className)}>
      <IconButton wrapperClasses={classes.button} size="md" label="Open Canvas" onClick={onClick}>
        <License />
      </IconButton>

      <h2 className={classes.heading}>{heading}</h2>
    </div>
  );
}
