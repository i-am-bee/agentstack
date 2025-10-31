/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AnimatePresence, motion } from 'framer-motion';

import { useApp } from '#contexts/App/index.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import classes from './AppName.module.scss';

export function AppName() {
  const {
    sidebarOpen,
    config: { appName },
  } = useApp();

  return (
    <AnimatePresence initial={false}>
      {!sidebarOpen && (
        <motion.p className={classes.root} {...fadeProps()}>
          {appName}
        </motion.p>
      )}
    </AnimatePresence>
  );
}
