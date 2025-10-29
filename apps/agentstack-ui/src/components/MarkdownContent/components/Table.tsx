/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { TableHTMLAttributes } from 'react';
import type { ExtraProps } from 'react-markdown';

import classes from './Table.module.scss';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function Table({ node, className, ...props }: TableHTMLAttributes<HTMLTableElement> & ExtraProps) {
  return (
    <div className={classes.root}>
      <table {...props} className={clsx(classes.table, className)} />
    </div>
  );
}
