/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export function useIsScrolled() {
  const scrollElementRef = useRef<HTMLDivElement>(null);
  const observeElementRef = useRef<HTMLDivElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  const scrollToBottom = useCallback(() => {
    const scrollElement = scrollElementRef.current;

    if (!scrollElement) {
      return;
    }

    scrollElement.scrollTo({
      top: scrollElement.scrollHeight,
    });

    setIsScrolled(false);
  }, []);

  useEffect(() => {
    const observeElement = observeElementRef.current;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsScrolled(!entry.isIntersecting);
      },
      { root: scrollElementRef.current },
    );

    if (observeElement) {
      observer.observe(observeElement);
    }

    return () => {
      if (observeElement) {
        observer.unobserve(observeElement);
      }
    };
  }, []);

  return {
    scrollElementRef,
    observeElementRef,
    isScrolled,
    scrollToBottom,
  };
}
