/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Close, ErrorFilled, InformationFilled } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { formatDistanceToNow } from 'date-fns';
import type { ValueTransition } from 'framer-motion';
import { AnimatePresence, motion } from 'framer-motion';
import { useCallback, useEffect, useState } from 'react';

import { NotificationMarkdownContent } from '#components/NotificationMarkdownContent/NotificationMarkdownContent.tsx';
import type { ToastWithKey } from '#contexts/Toast/toast-context.ts';
import { FADE_DURATION, FADE_EASE_ENTRANCE, FADE_EASE_EXIT, fadeProps } from '#utils/fadeProps.ts';

import classes from './Toast.module.scss';

interface Props {
  toast: ToastWithKey;
  onClose: () => void;
}

export function Toast({
  toast: { key, title, kind = 'info', timeout, icon, date, message, hideDate, renderMarkdown },
  onClose,
}: Props) {
  const [isOpen, setIsOpen] = useState(true);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  const handleUserInteraction = useCallback(() => {
    setHasUserInteracted(true);
  }, []);

  const Icon = icon ?? iconTypes[kind];

  useEffect(() => {
    if (!timeout || hasUserInteracted) {
      return;
    }

    const timeoutId = setTimeout(() => {
      handleClose();
    }, timeout);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [timeout, hasUserInteracted, handleClose]);

  return (
    <AnimatePresence onExitComplete={onClose}>
      {isOpen && (
        <motion.div
          key={key}
          role="status"
          className={clsx(classes.root, classes[`is-${kind}`])}
          layout="position"
          transition={{
            layout: springAnimation,
          }}
          onMouseEnter={handleUserInteraction}
          onPointerDown={handleUserInteraction}
          onFocusCapture={handleUserInteraction}
          onKeyDown={handleUserInteraction}
          {...fadeProps({
            hidden: {
              transform: 'translateX(100%)',
              transition: {
                duration: FADE_DURATION,
                ease: FADE_EASE_EXIT,
              },
            },
            visible: {
              transform: 'translateX(0)',
              transition: {
                duration: FADE_DURATION,
                ease: FADE_EASE_ENTRANCE,
                transform: springAnimation,
              },
            },
          })}
        >
          <header className={classes.header}>
            <IconButton kind="ghost" size="sm" label="Close" wrapperClasses={classes.closeButton} onClick={handleClose}>
              <Close />
            </IconButton>

            <Icon className={clsx(classes.icon, { [classes.defaultIcon]: !icon })} />

            {!hideDate && date && <ElapsedTime date={date} />}

            <h2 className={classes.heading}>{title}</h2>
          </header>

          {message &&
            (renderMarkdown ? (
              <NotificationMarkdownContent>{message}</NotificationMarkdownContent>
            ) : (
              <div className={classes.message}>{message}</div>
            ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

const springAnimation: ValueTransition = { type: 'spring', duration: FADE_DURATION * 2, bounce: 0.3 };

const iconTypes = {
  info: InformationFilled,
  error: ErrorFilled,
};

function ElapsedTime({ date }: { date: Date }) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      if (Date.now() - date.getTime() > MAX_REFRESH_INTERVAL_DURATION) {
        clearInterval(interval);
      }
      setTick((tick) => tick + 1);
    }, TIME_REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [date]);

  const millisecondsAgo = Date.now() - date.getTime();

  return (
    <time dateTime={date.toISOString()} className={classes.date}>
      {millisecondsAgo < JUST_NOW
        ? 'Just now'
        : millisecondsAgo > MAX_REFRESH_INTERVAL_DURATION
          ? 'More than an hour ago'
          : formatDistanceToNow(date, { addSuffix: true, includeSeconds: true })}
    </time>
  );
}

const JUST_NOW = 5_000; // 5 seconds
const TIME_REFRESH_INTERVAL = 5_000; // 5 seconds
const MAX_REFRESH_INTERVAL_DURATION = 3_600_000; // 1 hour
