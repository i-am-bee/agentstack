/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { useScrollableContainer } from './useScrollableContainer';

export function useAutoScroll(dependencies: unknown[]) {
  const ref = useRef<HTMLDivElement>(null);
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
      ref.current?.scrollIntoView();
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  return { ref };
}
