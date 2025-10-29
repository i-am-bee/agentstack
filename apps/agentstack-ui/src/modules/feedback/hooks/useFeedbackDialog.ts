/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UseFloatingOptions } from '@floating-ui/react';
import { autoUpdate, flip, offset, useDismiss, useFloating, useInteractions, useRole } from '@floating-ui/react';

import { FEEDBACK_DIALOG_OFFSET } from '../constants';

interface Props {
  open: UseFloatingOptions['open'];
  onOpenChange: UseFloatingOptions['onOpenChange'];
}

export function useFeedbackDialog({ open, onOpenChange }: Props) {
  const { refs, floatingStyles, context } = useFloating({
    placement: 'right-start',
    open,
    onOpenChange,
    whileElementsMounted: autoUpdate,
    middleware: [offset(FEEDBACK_DIALOG_OFFSET), flip()],
  });

  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'dialog' });

  const { getReferenceProps, getFloatingProps } = useInteractions([dismiss, role]);

  return {
    refs,
    floatingStyles,
    getReferenceProps,
    getFloatingProps,
  };
}
