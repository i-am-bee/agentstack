/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import clsx from 'clsx';
import type { CSSProperties, PropsWithChildren } from 'react';
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { useDebounceCallback } from 'usehooks-ts';

import { ExpandButton } from '#components/ExpandButton/ExpandButton.tsx';

import classes from './LineClampText.module.scss';

interface Props {
  lines: number;
  className?: string;
  buttonClassName?: string;
}

export function LineClampText({ lines, className, buttonClassName, children }: PropsWithChildren<Props>) {
  const id = useId();
  const textRef = useRef<HTMLElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showButton, setShowButton] = useState(false);

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
    <span className={clsx(classes.root, className)}>
      <span
        ref={textRef}
        id={id}
        className={clsx({ [classes.clamped]: !isExpanded })}
        style={{ '--line-clamp-lines': lines } as CSSProperties}
      >
        {children}
      </span>

      {showButton && (
        <span className={clsx(classes.button, buttonClassName)}>
          <ExpandButton onClick={() => setIsExpanded((state) => !state)} aria-controls={id} aria-expanded={isExpanded}>
            {isExpanded ? 'View less' : 'View more'}
          </ExpandButton>
        </span>
      )}
    </span>
  );
}
