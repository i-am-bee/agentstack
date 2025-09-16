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

import { useAgentRun } from '../contexts/agent-run';

interface Props {
  containerRef: RefObject<HTMLElement | null>;
}

export function useRunSettingsDialog({ containerRef }: Props) {
  const { hasMessages } = useAgentRun();
  const [isOpen, setIsOpen] = useState(false);

  const { refs, floatingStyles, context } = useFloating({
    placement: hasMessages ? 'top-start' : 'bottom-start',
    open: isOpen,
    onOpenChange: setIsOpen,
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(hasMessages ? OFFSET_CHAT : OFFSET_LANDING),
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

const OFFSET_LANDING = {
  mainAxis: 20,
  crossAxis: -12,
};
const OFFSET_CHAT = {
  mainAxis: 56,
  crossAxis: -12,
};
