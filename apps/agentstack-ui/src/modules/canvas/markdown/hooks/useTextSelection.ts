/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect } from 'react';

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
  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const handleMouseUp = () => {
      // Use requestAnimationFrame to ensure selection is updated
      requestAnimationFrame(() => {
        const selection = window.getSelection();
        const selectedText = selection?.toString().trim();

        if (!selection || selection.isCollapsed || selection.rangeCount === 0 || !selectedText) {
          onSelectionChange(null);
          return;
        }

        const range = selection.getRangeAt(0);
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
      });
    };

    container.addEventListener('mouseup', handleMouseUp);

    return () => {
      container.removeEventListener('mouseup', handleMouseUp);
    };
  }, [containerRef, onSelectionChange]);
}
