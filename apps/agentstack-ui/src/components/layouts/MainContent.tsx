/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import clsx from 'clsx';
import type { PropsWithChildren, ReactNode } from 'react';
import { mergeRefs } from 'react-merge-refs';

import { useIsScrolled } from '#hooks/useIsScrolled.ts';
import { useScrollbar } from '#hooks/useScrollbar.ts';

import classes from './MainContent.module.scss';

export interface MainContentProps extends PropsWithChildren {
  spacing?: 'sm' | 'md' | 'lg' | false;
  scrollable?: boolean;
  className?: string;
  footer?: ReactNode;
}

export function MainContent({ spacing = 'lg', scrollable = true, className, footer, children }: MainContentProps) {
  const { scrollElementRef, observeElementRef, isScrolled } = useIsScrolled();
  const { ref: scrollbarRef, ...scrollbarProps } = useScrollbar();

  const spacingClassName = spacing ? classes[spacing] : null;

  return (
    <div
      ref={mergeRefs([scrollbarRef, scrollElementRef])}
      className={clsx(
        classes.root,
        spacingClassName,
        {
          [classes.scrollable]: scrollable,
          [classes.hasFooter]: Boolean(footer),
        },
        className,
      )}
      {...scrollbarProps}
      data-scrolled={isScrolled}
    >
      <div className={classes.topRef} ref={observeElementRef} />

      <div className={classes.body}>{children}</div>

      {footer}
    </div>
  );
}
