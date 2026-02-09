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
  autoExpandOnContentChange?: boolean;
}

enum OverflowState {
  Unknown = 'unknown',
  Fits = 'fits',
  Clamped = 'clamped',
}

export function LineClampText({
  lines,
  iconButton,
  className,
  buttonClassName,
  useBlockElement,
  autoExpandOnContentChange,
  children,
}: PropsWithChildren<Props>) {
  const id = useId();
  const textRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLSpanElement>(null);
  const initialOverflowStateRef = useRef<OverflowState>(OverflowState.Unknown);

  const [isExpanded, setIsExpanded] = useState(false);
  const [overflowDetected, setOverflowDetected] = useState(false);

  const showButton = (isExpanded || overflowDetected) && initialOverflowStateRef.current !== OverflowState.Fits;

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

    if (isExpanded || !textElement || !sentinelElement) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        const isOverflowing = !entry.isIntersecting;

        setOverflowDetected(isOverflowing);

        if (initialOverflowStateRef.current === OverflowState.Unknown) {
          initialOverflowStateRef.current = isOverflowing ? OverflowState.Clamped : OverflowState.Fits;
        }

        if (autoExpandOnContentChange && initialOverflowStateRef.current === OverflowState.Fits && isOverflowing) {
          setIsExpanded(true);
        }
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
  }, [autoExpandOnContentChange, isExpanded]);

  return (
    <Component className={clsx(classes.root, className, { [classes.useBlockElement]: useBlockElement })}>
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
