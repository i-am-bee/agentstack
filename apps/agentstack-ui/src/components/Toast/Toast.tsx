/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Close, ErrorFilled, InformationFilled } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { formatDistanceToNow } from 'date-fns';
import { useCallback, useEffect, useRef, useState } from 'react';

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import type { Toast } from '#contexts/Toast/toast-context.ts';

import classes from './Toast.module.scss';

interface Props {
  toast: Toast;
  onClose: () => void;
}

export function Toast({
  toast: { title, kind = 'info', timeout, icon, date, message, hideDate, renderMarkdown },
  onClose,
}: Props) {
  const [isOpen, setIsOpen] = useState(true);
  const savedOnClose = useRef(onClose);

  const handleCloseClick = useCallback(() => {
    onClose();
    setIsOpen(false);
  }, [onClose]);

  const Icon = icon ?? iconTypes[kind];

  useEffect(() => {
    savedOnClose.current = onClose;
  });

  useEffect(() => {
    if (!timeout) {
      return;
    }

    const timeoutId = setTimeout(() => {
      setIsOpen(false);

      savedOnClose.current();
    }, timeout);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [timeout]);

  if (!isOpen) {
    return null;
  }

  return (
    <div role="status" className={clsx(classes.root, classes[`is-${kind}`])}>
      <header className={classes.header}>
        <IconButton
          kind="ghost"
          size="sm"
          label="Close"
          wrapperClasses={classes.closeButton}
          onClick={handleCloseClick}
        >
          <Close />
        </IconButton>

        <Icon className={clsx(classes.icon, { [classes.defaultIcon]: !icon })} />

        {!hideDate && date && <ElapsedTime date={date} />}

        <h2 className={classes.heading}>{title}</h2>
      </header>

      {message &&
        (renderMarkdown ? (
          <LineClampText lines={4} useBlockElement>
            <MarkdownContent>{message}</MarkdownContent>
          </LineClampText>
        ) : (
          <div>{message}</div>
        ))}
    </div>
  );
}

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
const TIME_REFRESH_INTERVAL = 1_000; // 10 seconds
const MAX_REFRESH_INTERVAL_DURATION = 3_600_000; // 1 hour
