/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UseDismissProps, UseFloatingOptions } from '@floating-ui/react';
import {
  autoUpdate,
  flip,
  offset,
  useClick,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
} from '@floating-ui/react';

import { PROMPT_EXAMPLES_DIALOG_OFFSET } from '../constants';

interface Props {
  open: UseFloatingOptions['open'];
  onOpenChange: UseFloatingOptions['onOpenChange'];
  outsidePressDismiss: UseDismissProps['outsidePress'];
}

export function usePromptExamplesDialog({ open, onOpenChange, outsidePressDismiss }: Props) {
  const { refs, floatingStyles, context, placement } = useFloating({
    placement: 'bottom-start',
    open,
    onOpenChange,
    whileElementsMounted: autoUpdate,
    middleware: [offset(PROMPT_EXAMPLES_DIALOG_OFFSET), flip()],
  });

  const click = useClick(context);
  const dismiss = useDismiss(context, { outsidePress: outsidePressDismiss });
  const role = useRole(context, { role: 'dialog' });

  const { getReferenceProps, getFloatingProps } = useInteractions([click, dismiss, role]);

  return {
    refs,
    floatingStyles,
    placement,
    getReferenceProps,
    getFloatingProps,
  };
}
