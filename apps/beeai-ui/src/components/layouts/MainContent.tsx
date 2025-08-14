/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import clsx from 'clsx';
import type { PropsWithChildren, ReactNode } from 'react';
import { mergeRefs } from 'react-merge-refs';

import { useIsScrolled } from '#hooks/useIsScrolled.ts';
import { useScrollbarWidth } from '#hooks/useScrollbarWidth.ts';
import { createScrollbarStyles } from '#utils/createScrollbarStyles.ts';

import classes from './MainContent.module.scss';

export interface MainContentProps extends PropsWithChildren {
  spacing?: 'md' | 'lg';
  scrollable?: boolean;
  className?: string;
  footer?: ReactNode;
}

export function MainContent({ spacing = 'lg', scrollable = true, className, footer, children }: MainContentProps) {
  const { scrollElementRef, observeElementRef, isScrolled } = useIsScrolled();
  const { ref: scrollbarRef, scrollbarWidth } = useScrollbarWidth();

  return (
    <div
      ref={mergeRefs([scrollbarRef, scrollElementRef])}
      className={clsx(
        classes.root,
        {
          [classes[spacing]]: spacing,
          [classes.scrollable]: scrollable,
          [classes.hasFooter]: Boolean(footer),
        },
        className,
      )}
      {...createScrollbarStyles({ width: scrollbarWidth })}
      data-scrolled={isScrolled}
    >
      <div className={classes.topRef} ref={observeElementRef} />

      <div className={classes.body}>{children}</div>

      {footer}
    </div>
  );
}
