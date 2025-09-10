/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  autoUpdate,
  offset,
  size,
  useClick,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
} from '@floating-ui/react';
import type { RefObject } from 'react';
import { useState } from 'react';

interface Props {
  containerRef: RefObject<HTMLElement | null>;
}

export function useRunSettingsDialog({ containerRef }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const { refs, floatingStyles, context } = useFloating({
    placement: 'bottom-start',
    open: isOpen,
    onOpenChange: setIsOpen,
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(OFFSET),
      size({
        apply({ elements }) {
          const container = containerRef.current;

          if (container) {
            Object.assign(elements.floating.style, {
              maxWidth: `${container.offsetWidth}px`,
            });
          }
        },
      }),
    ],
  });

  const click = useClick(context);
  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'dialog' });

  const { getReferenceProps, getFloatingProps } = useInteractions([click, dismiss, role]);

  return {
    isOpen,
    refs,
    floatingStyles,
    context,
    getReferenceProps,
    getFloatingProps,
  };
}

const OFFSET = {
  mainAxis: 20,
  crossAxis: -12,
};
