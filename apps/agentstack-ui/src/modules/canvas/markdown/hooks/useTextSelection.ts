/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import debounce from 'lodash/debounce';
import { useCallback, useEffect } from 'react';

export interface TextSelectionInfo {
  text: string;
  range: Range;
  rects: DOMRect[];
  firstVisibleRect?: DOMRect;
}

interface Props {
  containerRef: React.RefObject<HTMLElement | null>;
  onSelectionChange: (selection: TextSelectionInfo | null) => void;
}

export function useTextSelection({ containerRef, onSelectionChange }: Props) {
  const processSelection = useCallback(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const selection = window.getSelection();
    const selectedText = selection?.toString().trim();

    if (!selection || selection.isCollapsed || selection.rangeCount === 0 || !selectedText) {
      onSelectionChange(null);
      return;
    }

    const range = selection.getRangeAt(0).cloneRange();

    if (!container.contains(range.commonAncestorContainer)) {
      onSelectionChange(null);
      return;
    }

    const rects = Array.from(range.getClientRects());
    const firstVisibleRect = rects.find(({ width, height }) => width > 1 && height > 1);

    onSelectionChange({
      text: selectedText,
      range,
      rects,
      firstVisibleRect,
    });
  }, [containerRef, onSelectionChange]);

  useEffect(() => {
    const debouncedProcessSelection = debounce(processSelection, SELECTION_DEBOUNCE_MS);

    document.addEventListener('selectionchange', debouncedProcessSelection);

    return () => {
      debouncedProcessSelection.cancel();
      document.removeEventListener('selectionchange', debouncedProcessSelection);
    };
  }, [processSelection]);
}

const SELECTION_DEBOUNCE_MS = 100;
