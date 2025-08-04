/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';
import { mergeRefs } from 'react-merge-refs';

import { AppFooter } from '#components/layouts/AppFooter.tsx';
import { useIsScrolled } from '#hooks/useIsScrolled.ts';
import { useScrollbarWidth } from '#hooks/useScrollbarWidth.ts';
import { useToTopButton } from '#hooks/useToTopButton.ts';
import { createScrollbarStyles } from '#utils/createScrollbarStyles.ts';

import { ToTopButton } from '../ToTopButton/ToTopButton';
import classes from './MainContentView.module.scss';

export interface MainContentViewProps extends PropsWithChildren {
  spacing?: 'md' | 'lg';
  scrollable?: boolean;
  enableToTopButton?: boolean;
  showFooter?: boolean;
  className?: string;
}

export function MainContentView({
  spacing = 'lg',
  scrollable = true,
  enableToTopButton,
  showFooter,
  className,
  children,
}: MainContentViewProps) {
  const { scrollElementRef, observeElementRef, isScrolled } = useIsScrolled();
  const { ref: toTopRef, showButton, handleToTopClick } = useToTopButton({ enabled: enableToTopButton });
  const { ref: scrollbarRef, scrollbarWidth } = useScrollbarWidth();

  return (
    <div
      ref={mergeRefs([toTopRef, scrollbarRef, scrollElementRef])}
      className={clsx(
        classes.root,
        {
          [classes[spacing]]: spacing,
          [classes.scrollable]: scrollable,
        },
        className,
      )}
      {...createScrollbarStyles({ width: scrollbarWidth })}
      data-scrolled={isScrolled}
    >
      <div className={classes.topRef} ref={observeElementRef} />

      <div className={classes.body}>{children}</div>

      {showButton && <ToTopButton onClick={handleToTopClick} />}

      {showFooter && <AppFooter className={classes.footer} />}
    </div>
  );
}
