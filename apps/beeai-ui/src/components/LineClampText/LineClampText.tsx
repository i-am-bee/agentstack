/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { OverflowMenuHorizontal } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import type { CSSProperties, PropsWithChildren } from 'react';
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { useDebounceCallback } from 'usehooks-ts';

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
  const [isExpanded, setIsExpanded] = useState(false);
  const [showButton, setShowButton] = useState(false);

  const Component = useBlockElement ? 'div' : 'span';
  const buttonProps = {
    onClick: () => setIsExpanded((state) => !state),
    'aria-controls': id,
    'aria-expanded': isExpanded,
  };
  const buttonLabel = isExpanded ? 'View less' : 'View more';

  const checkOverflow = useCallback(() => {
    const element = textRef.current;

    if (!element) {
      return;
    }

    const { scrollHeight } = element;

    if (scrollHeight === 0) {
      return;
    }

    const lineHeight = parseFloat(getComputedStyle(element).lineHeight);
    const height = lineHeight * lines;

    if (scrollHeight > height) {
      setShowButton(true);
    } else {
      setShowButton(false);
    }
  }, [lines]);

  const debouncedCheckOverflow = useDebounceCallback(checkOverflow, 200);

  useEffect(() => {
    const element = textRef.current;

    if (!element) {
      return;
    }

    const resizeObserver = new ResizeObserver(() => {
      debouncedCheckOverflow();
    });

    resizeObserver.observe(element);

    return () => {
      if (element) {
        resizeObserver.unobserve(element);
      }
    };
  }, [debouncedCheckOverflow]);

  useEffect(() => {
    checkOverflow();
  }, [checkOverflow]);

  return (
    <Component className={clsx(classes.root, className)}>
      <Component
        ref={textRef}
        id={id}
        className={clsx({ [classes.clamped]: !isExpanded })}
        style={{ '--line-clamp-lines': lines } as CSSProperties}
      >
        {children}
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
