/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { noop } from '#utils/helpers.ts';

interface Props {
  enabled?: boolean;
}

export function useToTopButton({ enabled = true }: Props = {}) {
  const ref = useRef<HTMLDivElement>(null);
  const [showButton, setShowButton] = useState(false);

  const handleScroll = useCallback((event: Event) => {
    const { scrollTop } = event.target as HTMLDivElement;

    setShowButton(scrollTop > SCROLLED_OFFSET);
  }, []);

  const handleToTopClick = useCallback(() => {
    const element = ref.current;

    if (element) {
      element.scrollTo({ top: 0 });
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const element = ref.current;

    if (element) {
      element.addEventListener('scroll', handleScroll);
    }

    return () => {
      if (element) {
        element.removeEventListener('scroll', handleScroll);
      }
    };
  }, [handleScroll, enabled]);

  return enabled
    ? {
        ref,
        showButton,
        handleToTopClick,
      }
    : {
        ref,
        showButton: false,
        handleToTopClick: noop,
      };
}

const SCROLLED_OFFSET = 48;
