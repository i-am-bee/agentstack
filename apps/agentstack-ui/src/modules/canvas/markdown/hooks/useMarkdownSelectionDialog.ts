/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { autoUpdate, offset, useDismiss, useFloating, useInteractions, useRole } from '@floating-ui/react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { type TextSelectionInfo, useTextSelection } from './useTextSelection';

export function useMarkdownSelectionDialog(containerRef: React.RefObject<HTMLElement | null>) {
  const [selection, setSelection] = useState<TextSelectionInfo | null>(null);

  const handleSelectionChange = useCallback((selection: TextSelectionInfo | null) => {
    if (!selection || !selection.firstVisibleRect) {
      return;
    }

    setSelection(selection);
    const highlight = new Highlight(selection.range);
    CSS.highlights.set(HIGHLIGHT_NAME, highlight);
  }, []);

  useTextSelection({ containerRef, onSelectionChange: handleSelectionChange });

  const containerRect = containerRef.current?.getBoundingClientRect();

  const clearSelection = useCallback(() => {
    setSelection(null);
    CSS.highlights.delete(HIGHLIGHT_NAME);
  }, []);

  useEffect(() => {
    return () => {
      clearSelection();
    };
  }, [clearSelection]);

  const firstVisibleRect = selection?.firstVisibleRect ?? null;

  const offsets = useMemo(() => {
    if (!firstVisibleRect || !containerRect) {
      return null;
    }
    return { top: containerRect.top - firstVisibleRect.top, left: firstVisibleRect.left - containerRect.left };
  }, [firstVisibleRect, containerRect]);
  const isOpen = Boolean(selection);

  const { refs, floatingStyles, context } = useFloating({
    placement: 'top-start',
    open: isOpen,
    onOpenChange: (open) => !open && clearSelection(),
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
    selection,
    refs,
    floatingStyles,
    context,
    getFloatingProps,
    close: clearSelection,
  };
}

export type MarkdownSelectionDialogReturn = ReturnType<typeof useMarkdownSelectionDialog>;

const SELECTION_BLOCK_OFFSET = 8;
const HIGHLIGHT_NAME = 'canvas-highlight';
