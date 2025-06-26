/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { moderate02 } from '@carbon/motion';
import { AnimatePresence, motion } from 'framer-motion';
import { type PropsWithChildren, type ReactNode, useEffect } from 'react';

import { MainContent } from '#components/layouts/MainContent.tsx';
import type { MainContentViewProps } from '#components/MainContentView/MainContentView.tsx';
import { useApp } from '#contexts/App/index.ts';
import { useScrollbarWidth } from '#hooks/useScrollbarWidth.ts';
import { createScrollbarStyles } from '#utils/createScrollbarStyles.ts';

import classes from './SplitPanesView.module.scss';

interface Props {
  leftPane: ReactNode;
  rightPane: ReactNode;
  mainContent?: ReactNode;
  isSplit?: boolean;
  spacing?: MainContentViewProps['spacing'];
}

export function SplitPanesView({ leftPane, rightPane, mainContent, isSplit, spacing }: Props) {
  const { ref: leftPaneRef, scrollbarWidth } = useScrollbarWidth();
  const { agentDetailOpen, navigationOpen, hideAgentDetail, setNavigationOpen, setCloseNavOnClickOutside } = useApp();

  useEffect(() => {
    if (isSplit) {
      hideAgentDetail?.();
      setNavigationOpen?.(false);
    }
  }, [isSplit, hideAgentDetail, setNavigationOpen]);

  useEffect(() => {
    if (navigationOpen && isSplit) {
      setCloseNavOnClickOutside?.(true);
    } else {
      setCloseNavOnClickOutside?.(false);
    }

    return () => {
      setCloseNavOnClickOutside?.(false);
    };
  }, [isSplit, navigationOpen, setCloseNavOnClickOutside]);

  return (
    <AnimatePresence mode="wait">
      {isSplit && !agentDetailOpen ? (
        <Wrapper key="split-view" className={classes.splitView} immediateExit>
          <div className={classes.leftPane} ref={leftPaneRef} {...createScrollbarStyles({ width: scrollbarWidth })}>
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
