/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import classes from './TableView.module.scss';

interface Props {
  description?: string;
}

export function TableView({ description, children }: PropsWithChildren<Props>) {
  return (
    <div className={classes.root}>
      {description && <p className={classes.description}>{description}</p>}

      <div className={classes.table}>{children}</div>
    </div>
  );
}
