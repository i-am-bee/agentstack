/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import type { RefCallback } from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useDebounceCallback } from 'usehooks-ts';

export function useScrollbarWidth() {
  const [scrollbarWidth, setScrollbarWidth] = useState<number>(0);
  const [element, setElement] = useState<HTMLElement | null>(null);

  const checkScrollbar = useCallback((element: HTMLElement) => {
    const scrollbarWidth = element.offsetWidth - element.clientWidth;

    setScrollbarWidth(scrollbarWidth);
  }, []);

  const debouncedCheckScrollbar = useDebounceCallback(checkScrollbar, 200);

  const ref: RefCallback<HTMLElement> = useCallback(
    (element) => {
      if (!element) {
        return;
      }

      setElement(element);
      checkScrollbar(element);
    },
    [checkScrollbar],
  );

  useEffect(() => {
    if (!element) {
      return;
    }

    const resizeObserver = new ResizeObserver(() => {
      debouncedCheckScrollbar(element);
    });

    resizeObserver.observe(element);

    return () => resizeObserver.unobserve(element);
  }, [element, debouncedCheckScrollbar]);

  return { ref, scrollbarWidth };
}
