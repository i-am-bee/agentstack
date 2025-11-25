/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';

export interface TextSelectionInfo {
  text: string;
  range: Range;
  rects: DOMRect[];
  firstVisibleRect?: DOMRect;
}

export function useTextSelection(containerRef: React.RefObject<HTMLElement | null>) {
  const [selection, setSelection] = useState<TextSelectionInfo | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const validateSelection = () => {
      const selection = window.getSelection();
      const selectedText = selection?.toString().trim();

      if (!selection || selection.isCollapsed || selection.rangeCount === 0 || !selectedText) {
        setSelection(null);
        return false;
      }

      const range = selection.getRangeAt(0);
      if (!container.contains(range.commonAncestorContainer)) {
        setSelection(null);
        return false;
      }

      return true;
    };

    const handleMouseUp = () => {
      const selection = window.getSelection();

      if (!selection || !validateSelection()) {
        return;
      }

      const selectedText = selection.toString().trim();

      const range = selection.getRangeAt(0);
      const rects = Array.from(range.getClientRects());

      const firstVisibleRect = rects.find(({ width, height }) => width > 1 && height > 1);

      setSelection({
        text: selectedText,
        range,
        rects,
        firstVisibleRect,
      });
    };

    // Listen to both selectionchange and mouseup (for better responsiveness)
    document.addEventListener('selectionchange', validateSelection);
    container.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('selectionchange', validateSelection);
      container.removeEventListener('mouseup', handleMouseUp);
    };
  }, [containerRef]);

  return selection;
}
