/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import type { MouseEventHandler } from 'react';

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import classes from './TrajectoryButton.module.scss';

interface Props {
  isOpen?: boolean;
  onClick?: MouseEventHandler;
  message?: string;
  currentTrajectory?: UITrajectoryPart | null;
}

export function TrajectoryButton({ isOpen, message, currentTrajectory, onClick }: Props) {
  const displayMessage = message ?? currentTrajectory?.title ?? currentTrajectory?.content ?? 'Activity';

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
        >
          {displayMessage}
        </motion.span>
      </AnimatePresence>
    </Button>
  );
}
