/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AnimatePresence, motion } from 'framer-motion';

import { fadeProps } from '#utils/fadeProps.ts';

import classes from './Toolbar.module.scss';

interface Props {
  isVisible?: boolean;
}

export function Toolbar({ isVisible }: Props) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.aside {...fadeProps()} className={classes.root}>
          Toolbar
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
