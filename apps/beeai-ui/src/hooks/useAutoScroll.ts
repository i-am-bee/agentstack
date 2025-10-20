/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { animate } from 'framer-motion';
import { useCallback, useEffect, useRef, useState } from 'react';

import { useScrollableContainer } from './useScrollableContainer';

export function useAutoScroll<T extends HTMLElement = HTMLDivElement>(
  dependencies: unknown[],
  { duration }: { duration?: number } = {},
) {
  const ref = useRef<T>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const scrollableContainer = useScrollableContainer(ref.current);

  const handleWheel = useCallback(
    (event: WheelEvent) => {
      if (!scrollableContainer) {
        return;
      }

      const scrolledToBottom =
        scrollableContainer.scrollHeight - scrollableContainer.scrollTop === scrollableContainer.clientHeight;

      if (event.deltaY < 0) {
        setShouldAutoScroll(false);
      } else if (scrolledToBottom) {
        setShouldAutoScroll(true);
      }
    },
    [scrollableContainer],
  );

  useEffect(() => {
    if (scrollableContainer) {
      scrollableContainer.addEventListener('wheel', handleWheel);
    }

    return () => {
      if (scrollableContainer) {
        scrollableContainer.removeEventListener('wheel', handleWheel);
      }
    };
  }, [scrollableContainer, handleWheel]);

  useEffect(() => {
    if (shouldAutoScroll) {
      if (duration && ref.current && scrollableContainer) {
        const scrollFrom = scrollableContainer.scrollTop;
        const scrollTo = ref.current.getBoundingClientRect().bottom;
        console.log({ scrollTo });

        animate(scrollFrom, scrollTo, {
          duration,
          ease: 'easeInOut',
          onUpdate: (value) => scrollableContainer.scrollTo(0, value),
        });
      } else {
        ref.current?.scrollIntoView();
      }
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  return { ref };
}
