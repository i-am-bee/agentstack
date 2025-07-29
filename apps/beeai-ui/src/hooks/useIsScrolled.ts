/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useRef } from 'react';
import { useIntersectionObserver } from 'usehooks-ts';

export function useIsScrolled() {
  const scrollElementRef = useRef<HTMLDivElement>(null);

  const { isIntersecting, ref: observeElementRef } = useIntersectionObserver();
  const isScrolled = !isIntersecting;

  const scrollToBottom = useCallback(() => {
    const scrollElement = scrollElementRef.current;

    if (!scrollElement) {
      return;
    }

    scrollElement.scrollTo({
      top: scrollElement.scrollHeight,
    });
  }, []);

  return {
    scrollElementRef,
    observeElementRef,
    isScrolled,
    scrollToBottom,
  };
}
