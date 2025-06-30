/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { forwardRef, type PropsWithChildren } from 'react';

import classes from './SidePanel.module.scss';

interface Props {
  variant: 'left' | 'right';
  isOpen?: boolean;
  className?: string;
}

export const SidePanel = forwardRef<HTMLElement, PropsWithChildren<Props>>(function SidePanel(
  { variant, isOpen, className, children },
  ref,
) {
  return (
    <aside
      ref={ref}
      className={clsx(
        classes.root,
        [classes[variant]],
        {
          [classes.isOpen]: isOpen,
        },
        className,
      )}
    >
      <div className={classes.content}>{children}</div>
    </aside>
  );
});
