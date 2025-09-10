/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { isNotNull } from '@i-am-bee/beeai-ui';
import debounce from 'lodash/debounce';
import type { MouseEvent } from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';

interface Section {
  href: string;
  element: HTMLElement;
  offset: number;
}

interface Props {
  scrollableContainer: HTMLElement | null;
  items: { href: string }[];
}

export function useSections({ scrollableContainer, items }: Props) {
  const [activeHref, setActiveHref] = useState<string | null>(null);
  const [sections, setSections] = useState<Section[]>([]);

  const handleClick = useCallback(
    (event: MouseEvent<HTMLAnchorElement>, href: string) => {
      const element = sections.find((section) => section.href === href)?.element;

      if (!element) {
        return;
      }

      event.preventDefault();

      element.scrollIntoView();
    },
    [sections],
  );

  const handleResize = useCallback(() => {
    const sections = items
      .map(({ href }) => {
        if (!href.startsWith('#')) {
          return null;
        }

        const id = href.slice(1);
        const element = document.getElementById(id);

        if (!element) {
          return null;
        }

        const offset = Math.floor(element.offsetTop);

        return {
          href,
          element,
          offset,
        };
      })
      .filter(isNotNull);

    setSections(sections);
  }, [items]);

  const handleScroll = useCallback(() => {
    if (!scrollableContainer) {
      return;
    }

    const scrollTop = Math.ceil(scrollableContainer.scrollTop);
    const scrolledSection = sections.find((section, index) => {
      const { offset } = section;
      const nextSection = sections[index + 1];

      if (scrollTop < offset) {
        return;
      }

      return nextSection ? scrollTop < nextSection.offset : true;
    });

    setActiveHref(scrolledSection ? scrolledSection.href : null);
  }, [scrollableContainer, sections]);

  const debouncedHandleResize = useMemo(() => debounce(handleResize, 200), [handleResize]);

  useEffect(() => {
    if (!scrollableContainer) {
      return;
    }

    const resizeObserver = new ResizeObserver(() => {
      debouncedHandleResize();
    });

    resizeObserver.observe(scrollableContainer);

    return () => {
      if (scrollableContainer) {
        resizeObserver.unobserve(scrollableContainer);
      }
    };
  }, [scrollableContainer, debouncedHandleResize]);

  useEffect(() => {
    if (!scrollableContainer) {
      return;
    }

    scrollableContainer.addEventListener('scroll', handleScroll);

    return () => {
      scrollableContainer.removeEventListener('scroll', handleScroll);
    };
  }, [scrollableContainer, handleScroll]);

  useEffect(() => {
    handleResize();
  }, [handleResize]);

  return { activeHref, handleClick };
}
