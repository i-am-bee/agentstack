/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { rem } from '@carbon/layout';
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
import { useState } from 'react';

import { useAgentRun } from '../contexts/agent-run';

interface Props {
  maxWidth?: 'container' | { widthPx: number };
}

export function useRunSettingsDialog({ maxWidth = 'container' }: Props = {}) {
  const { hasMessages } = useAgentRun();
  const [isOpen, setIsOpen] = useState(false);

  const { refs, floatingStyles, context } = useFloating({
    placement: hasMessages ? 'top-start' : 'bottom-start',
    open: isOpen,
    onOpenChange: setIsOpen,
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(hasMessages ? OFFSET_CHAT : maxWidth === 'container' ? OFFSET_LANDING_CONTAINER : OFFSET_LANDING),
      size({
        apply({ elements }) {
          const container = elements.reference;

          if (maxWidth === 'container' && !container) {
            return;
          }

          const widthValue = maxWidth === 'container' ? container.getBoundingClientRect().width : maxWidth.widthPx;
          Object.assign(elements.floating.style, {
            maxWidth: rem(widthValue),
          });
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

export type RunSettingsDialogReturn = ReturnType<typeof useRunSettingsDialog>;

const OFFSET_LANDING = {
  mainAxis: 7,
  crossAxis: -12,
};
const OFFSET_LANDING_CONTAINER = {
  mainAxis: -4,
  crossAxis: 0,
};
const OFFSET_CHAT = {
  mainAxis: 8,
  crossAxis: 0,
};
