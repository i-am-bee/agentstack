/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';

export function useScrollableContainer(element: HTMLElement | null) {
  const [container, setContainer] = useState<HTMLElement | null>(null);

  useEffect(() => {
    if (element) {
      let parent = element.parentElement;

      while (parent) {
        const { overflowY } = window.getComputedStyle(parent);

        if (overflowY === 'scroll' || overflowY === 'auto') {
          setContainer(parent);

          return;
        }

        parent = parent.parentElement;
      }
    }
  }, [element]);

  return container;
}
