/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import type { MouseEventHandler } from 'react';

import { fadeProps } from '#utils/fadeProps.ts';

import classes from './TrajectoryButton.module.scss';

interface Props {
  isOpen?: boolean;
  onClick?: MouseEventHandler;
  message?: string;
}

export function TrajectoryButton({ isOpen, message, onClick }: Props) {
  const displayMessage = message ?? 'Activity';

  return (
    <Button
      kind="ghost"
      size="sm"
      renderIcon={ChevronDown}
      className={clsx(classes.root, { [classes.isOpen]: isOpen })}
      onClick={onClick}
    >
      <AnimatePresence mode="wait">
        <motion.span
          {...fadeProps({
            hidden: {
              y: -4,
              transition: { duration: 0.3 },
            },
            visible: {
              y: 0,
              transition: { duration: 0.3 },
            },
          })}
          key={displayMessage}
          className={classes.message}
        >
          {displayMessage}
        </motion.span>
      </AnimatePresence>
    </Button>
  );
}
