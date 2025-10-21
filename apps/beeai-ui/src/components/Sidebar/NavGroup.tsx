/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import { useScrollbar } from '#hooks/useScrollbar.ts';

import classes from './NavGroup.module.scss';

interface Props extends PropsWithChildren {
  heading?: string;
  className?: string;
}

export function NavGroup({ heading, className, children }: Props) {
  const scrollbarProps = useScrollbar();

  return (
    <nav className={clsx(classes.root, className)}>
      {heading && (
        <div className={classes.header}>
          <h2 className={classes.heading}>{heading}</h2>
        </div>
      )}

      <div className={classes.body} {...scrollbarProps}>
        {children}
      </div>
    </nav>
  );
}
