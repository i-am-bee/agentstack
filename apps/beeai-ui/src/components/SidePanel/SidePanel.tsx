/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import { useScrollbar } from '#hooks/useScrollbar.ts';

import classes from './SidePanel.module.scss';

interface Props extends PropsWithChildren {
  isOpen?: boolean;
  className?: string;
}

export function SidePanel({ isOpen, className, children }: Props) {
  const scrollbarProps = useScrollbar();

  return (
    <aside className={clsx(classes.root, { [classes.isOpen]: isOpen }, className)}>
      <div className={classes.content} {...scrollbarProps}>
        {children}
      </div>
    </aside>
  );
}
