/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import type { ButtonBaseProps } from '@carbon/react';
import { Button } from '@carbon/react';

import classes from './ExpandButton.module.scss';

export function ExpandButton({ children, ...props }: Omit<ButtonBaseProps, 'ghost' | 'className'>) {
  return (
    <Button {...props} kind="ghost" className={classes.root}>
      <span>{children}</span>

      <ChevronDown />
    </Button>
  );
}
