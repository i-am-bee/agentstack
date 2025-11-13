/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { OverflowMenuHorizontal } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import type { CSSProperties, PropsWithChildren } from 'react';
import { useEffect, useId, useRef, useState } from 'react';

import { ExpandButton } from '#components/ExpandButton/ExpandButton.tsx';

import classes from './LineClampText.module.scss';

interface Props {
  lines: number;
  iconButton?: boolean;
  className?: string;
  buttonClassName?: string;
  useBlockElement?: boolean;
}

export function LineClampText({
  lines,
  iconButton,
  className,
  buttonClassName,
  useBlockElement,
  children,
}: PropsWithChildren<Props>) {
  const id = useId();
  const textRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLSpanElement>(null);

  const [isExpanded, setIsExpanded] = useState(false);
  const [overflowDetected, setOverflowDetected] = useState(false);

  const showButton = isExpanded || overflowDetected;

  const Component = useBlockElement ? 'div' : 'span';
  const buttonProps = {
    onClick: () => setIsExpanded((state) => !state),
    'aria-controls': id,
    'aria-expanded': isExpanded,
  };
  const buttonLabel = isExpanded ? 'View less' : 'View more';

  useEffect(() => {
    const textElement = textRef.current;
    const sentinelElement = sentinelRef.current;

    if (!textElement || !sentinelElement) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        setOverflowDetected(!entry.isIntersecting);
      },
      {
        root: textElement,
        threshold: 1,
      },
    );

    observer.observe(sentinelElement);

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <Component className={clsx(classes.root, className)}>
      <Component
        ref={textRef}
        id={id}
        className={clsx({ [classes.clamped]: !isExpanded })}
        style={{ '--line-clamp-lines': lines } as CSSProperties}
      >
        {children}

        <span ref={sentinelRef} className={classes.sentinel} />
      </Component>

      {showButton && (
        <Component className={clsx(classes.button, buttonClassName)}>
          {iconButton ? (
            <IconButton {...buttonProps} kind="tertiary" label={buttonLabel}>
              <OverflowMenuHorizontal />
            </IconButton>
          ) : (
            <ExpandButton {...buttonProps}>{buttonLabel}</ExpandButton>
          )}
        </Component>
      )}
    </Component>
  );
}
