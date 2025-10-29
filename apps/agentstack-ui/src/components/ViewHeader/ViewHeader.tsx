/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren, ReactElement } from 'react';

import classes from './ViewHeader.module.scss';

interface Props {
  heading: string;
  label?: ReactElement;
}

export function ViewHeader({ heading, label, children }: PropsWithChildren<Props>) {
  return (
    <header className={classes.root}>
      {label ? <div className={classes.label}>{label}</div> : null}
      <div className={classes.body}>
        <h1 className={classes.heading}>{heading}</h1>

        {children && <div>{children}</div>}
      </div>
    </header>
  );
}
