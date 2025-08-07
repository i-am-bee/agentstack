/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ThumbsDown, ThumbsUp } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { FloatingPortal } from '@floating-ui/react';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';

import type { UIAgentMessage } from '#modules/messages/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { useFeedback } from '../hooks/useFeedback';
import { FeedbackVote } from '../types';
import { FeedbackForm } from './FeedbackForm';
import classes from './MessageFeedback.module.scss';

interface Props {
  message: UIAgentMessage;
  buttonWrapperClasses: string;
  onOpenChange: (formOpen: boolean) => void;
}

export function MessageFeedback({ message, buttonWrapperClasses, onOpenChange }: Props) {
  const { formOpen, currentVote, getVoteUpProps, getVoteDownProps, getDialogProps, getFormProps, positionRef } =
    useFeedback({ message, onOpenChange });

  const isVoteUp = currentVote === FeedbackVote.Up;
  const isVoteDown = currentVote === FeedbackVote.Down;

  return (
    <>
      <IconButton
        size="sm"
        kind="tertiary"
        label="I like this response"
        wrapperClasses={buttonWrapperClasses}
        className={clsx({ [classes.isVoted]: isVoteUp })}
        {...getVoteUpProps()}
      >
        <ThumbsUp />
      </IconButton>

      <IconButton
        size="sm"
        kind="tertiary"
        label="I dislike this response"
        wrapperClasses={buttonWrapperClasses}
        className={clsx({ [classes.isVoted]: isVoteDown })}
        {...getVoteDownProps()}
      >
        <ThumbsDown />
      </IconButton>

      <div ref={positionRef} className={classes.ref} />

      <AnimatePresence>
        {formOpen && (
          <FloatingPortal>
            <div {...getDialogProps()}>
              <motion.div {...fadeProps()} className={classes.dialog}>
                <FeedbackForm {...getFormProps()} />
              </motion.div>
            </div>
          </FloatingPortal>
        )}
      </AnimatePresence>
    </>
  );
}
