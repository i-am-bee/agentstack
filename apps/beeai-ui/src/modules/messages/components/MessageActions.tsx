/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { type RefObject, useState } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';
import { MessageFeedback } from '#modules/feedback/components/MessageFeedback.tsx';
import { fadeProps } from '#utils/fadeProps.ts';

import type { UIAgentMessage } from '../types';
import classes from './MessageActions.module.scss';

interface Props {
  isVisible: boolean;
  message: UIAgentMessage;
  contentRef: RefObject<HTMLElement | null>;
  className?: string;
}

export function MessageActions({ isVisible, message, contentRef, className }: Props) {
  const [feedbackFormOpen, setFeedbackFormOpen] = useState(false);

  const shouldShow = isVisible || feedbackFormOpen;

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.aside {...fadeProps()} className={clsx(classes.root, className)}>
          <MessageFeedback message={message} buttonWrapperClasses={classes.button} onOpenChange={setFeedbackFormOpen} />

          <CopyButton size="sm" kind="tertiary" wrapperClasses={classes.button} contentRef={contentRef} />
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
