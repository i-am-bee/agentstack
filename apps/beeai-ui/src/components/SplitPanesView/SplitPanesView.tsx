/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { moderate02 } from '@carbon/motion';
import { AnimatePresence, motion } from 'framer-motion';
import { type PropsWithChildren, type ReactNode, useEffect } from 'react';

import type { MainContentProps } from '#components/layouts/MainContent.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { useApp } from '#contexts/App/index.ts';
import { useScrollbar } from '#hooks/useScrollbar.ts';

import classes from './SplitPanesView.module.scss';

interface Props {
  leftPane: ReactNode;
  rightPane: ReactNode;
  mainContent?: ReactNode;
  isSplit?: boolean;
  spacing?: MainContentProps['spacing'];
}

export function SplitPanesView({ leftPane, rightPane, mainContent, isSplit, spacing }: Props) {
  const scrollbarProps = useScrollbar();
  const { activeSidePanel, closeSidebar, closeSidePanel } = useApp();

  useEffect(() => {
    if (isSplit) {
      closeSidebar();
      closeSidePanel();
    }
  }, [isSplit, closeSidebar, closeSidePanel]);

  return (
    <AnimatePresence mode="wait">
      {isSplit && !activeSidePanel ? (
        <Wrapper key="split-view" className={classes.splitView} immediateExit>
          <div className={classes.leftPane} {...scrollbarProps}>
            <div className={classes.content}>{leftPane}</div>
          </div>

          <div className={classes.rightPane}>
            <div className={classes.content}>{rightPane}</div>
          </div>
        </Wrapper>
      ) : (
        <MainContent spacing={spacing}>
          <Wrapper key="simple-view" className={classes.simpleView}>
            {mainContent || leftPane}
          </Wrapper>
        </MainContent>
      )}
    </AnimatePresence>
  );
}

interface WrapperProps {
  immediateExit?: boolean;
  className?: string;
}

function Wrapper({ immediateExit, className, children }: PropsWithChildren<WrapperProps>) {
  const duration = parseFloat(moderate02) / 1000;

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: immediateExit ? 0 : duration } }}
      transition={{ duration }}
    >
      {children}
    </motion.div>
  );
}
