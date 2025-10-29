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
  maxWidth?: number;
  blockOffset?: number;
}

export function useRunSettingsDialog({ maxWidth, blockOffset }: Props = {}) {
  const [isOpen, setIsOpen] = useState(false);
  const { hasMessages } = useAgentRun();

  const align = hasMessages ? 'top' : 'bottom';
  const alignWithContainer = !maxWidth;

  const { refs, floatingStyles, context } = useFloating({
    placement: `${align}-start`,
    open: isOpen,
    onOpenChange: setIsOpen,
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(() => {
        const offsets =
          align === 'top' ? OFFSET_ALIGN_TOP : alignWithContainer ? OFFSET_ALIGN_BOTTOM_CONTAINER : OFFSET_ALIGN_BOTTOM;
        if (blockOffset) {
          offsets.mainAxis = blockOffset;
        }

        return offsets;
      }, [align, alignWithContainer, blockOffset]),
      size(
        {
          apply({ elements }) {
            const container = elements.reference;
            const widthValue = !maxWidth ? container?.getBoundingClientRect().width : maxWidth;
            if (widthValue) {
              Object.assign(elements.floating.style, {
                maxWidth: rem(widthValue),
              });
            }
          },
        },
        [maxWidth],
      ),
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

const OFFSET_ALIGN_BOTTOM = {
  mainAxis: 7,
  crossAxis: -12,
};
const OFFSET_ALIGN_BOTTOM_CONTAINER = {
  mainAxis: -3,
  crossAxis: 0,
};
const OFFSET_ALIGN_TOP = {
  mainAxis: 8,
  crossAxis: 0,
};
