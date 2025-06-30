/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowUp } from '@carbon/icons-react';
import type { IconButtonProps } from '@carbon/react';
import { IconButton } from '@carbon/react';

import classes from './ToTopButton.module.scss';

interface Props {
  onClick?: IconButtonProps['onClick'];
}

export function ToTopButton({ onClick }: Props) {
  return (
    <div className={classes.root}>
      <IconButton label="To top" kind="tertiary" size="md" onClick={onClick}>
        <ArrowUp />
      </IconButton>
    </div>
  );
}
