/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AnimatePresence, motion } from 'framer-motion';

import { fadeProps } from '#utils/fadeProps.ts';

interface Props {
  isVisible?: boolean;
}

export function Toolbar({ isVisible }: Props) {
  return <AnimatePresence>{isVisible && <motion.aside {...fadeProps()}>Toolbar</motion.aside>}</AnimatePresence>;
}
