/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { autoUpdate, offset, shift, useDismiss, useFloating, useInteractions, useRole } from '@floating-ui/react';
import { useEffect, useMemo, useState } from 'react';

import type { TextSelectionInfo } from './useTextSelection';

interface Props {
  selection: TextSelectionInfo | null;
  containerRef: React.RefObject<HTMLElement | null>;
}

export function useMarkdownSelectionDialog({ selection: selectionProps, containerRef }: Props) {
  const [selection, setSelection] = useState<TextSelectionInfo | null>(selectionProps);

  const containerRect = containerRef.current?.getBoundingClientRect();

  useEffect(() => {
    const open = Boolean(selectionProps && containerRect && selectionProps.firstVisibleRect);

    if (open) {
      setSelection(selectionProps ?? null);
    }
  }, [containerRect, selectionProps]);

  const firstVisibleRect = selection?.firstVisibleRect ?? null;

  const offsets = useMemo(() => {
    if (!firstVisibleRect || !containerRect) {
      return null;
    }
    return { top: containerRect.top - firstVisibleRect.top, left: firstVisibleRect.left - containerRect.left };
  }, [firstVisibleRect, containerRect]);
  const isOpen = Boolean(selection);

  // Use the first rect as the reference for positioning
  const { refs, floatingStyles, context } = useFloating({
    placement: 'top-start',
    open: isOpen,
    onOpenChange: (open) => !open && setSelection(null),
    middleware: [
      offset(() => {
        if (offsets === null) {
          return {
            mainAxis: 0,
            crossAxis: 0,
          };
        }

        return {
          mainAxis: offsets.top + SELECTION_BLOCK_OFFSET,
          crossAxis: offsets.left,
        };
      }, [offsets]),
      shift({ padding: 8 }),
    ],
    whileElementsMounted: autoUpdate,
  });

  const role = useRole(context, { role: 'dialog' });
  const dismiss = useDismiss(context, {
    outsidePress: true,
    escapeKey: true,
  });

  const { getFloatingProps } = useInteractions([role, dismiss]);

  return {
    isOpen,
    refs,
    floatingStyles,
    context,
    getFloatingProps,
  };
}

export type MarkdownSelectionDialogReturn = ReturnType<typeof useMarkdownSelectionDialog>;

const SELECTION_BLOCK_OFFSET = 8;
