/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';
import { mergeRefs } from 'react-merge-refs';

import { AppFooter } from '#components/layouts/AppFooter.tsx';
import { useScrollbarWidth } from '#hooks/useScrollbarWidth.ts';
import { useToTopButton } from '#hooks/useToTopButton.ts';
import { createScrollbarStyles } from '#utils/createScrollbarStyles.ts';

import { ToTopButton } from '../ToTopButton/ToTopButton';
import classes from './MainContentView.module.scss';

export interface MainContentViewProps extends PropsWithChildren {
  spacing?: 'md' | 'lg';
  enableToTopButton?: boolean;
  showFooter?: boolean;
  limitHeight?: boolean;
  className?: string;
}

export function MainContentView({
  spacing = 'lg',
  enableToTopButton,
  showFooter,
  limitHeight,
  className,
  children,
}: MainContentViewProps) {
  const { ref: toTopRef, showButton, handleToTopClick } = useToTopButton({ enabled: enableToTopButton });
  const { ref: scrollbarRef, scrollbarWidth } = useScrollbarWidth();

  return (
    <div
      ref={mergeRefs([toTopRef, scrollbarRef])}
      className={clsx(classes.root, classes[spacing], className)}
      {...createScrollbarStyles({ width: scrollbarWidth })}
    >
      <div className={clsx(classes.body, limitHeight && classes.limitHeight)}>{children}</div>

      {showButton && <ToTopButton onClick={handleToTopClick} />}

      {showFooter && <AppFooter className={classes.footer} />}
    </div>
  );
}
