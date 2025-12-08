/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MD_END_INDEX_ATTR, MD_START_INDEX_ATTR } from '#components/MarkdownContent/rehype/rehypeSourcePosition.ts';
import type { UICanvasEditRequestParams } from '#modules/canvas/types.ts';

export type MarkdownSelection = Pick<UICanvasEditRequestParams, 'startIndex' | 'endIndex' | 'content'>;

export interface ElementWithSourcePosition {
  element: Element;
  start: number;
  end: number;
}

function findNearestElementWithPosition(node: Node): ElementWithSourcePosition | null {
  let current: Node | null = node;

  while (current) {
    if (current.nodeType === Node.ELEMENT_NODE) {
      const element = current as Element;
      const start = parseInt(element.getAttribute(MD_START_INDEX_ATTR) ?? '');
      const end = parseInt(element.getAttribute(MD_END_INDEX_ATTR) ?? '');

      if (!isNaN(start) && !isNaN(end)) {
        return { element, start, end };
      }
    }
    current = current.parentNode;
  }

  return null;
}

function getNodeOffsetWithin(rootElem: Element, node: Node, offset: number): number {
  let nodeOffset = 0;
  const walker = document.createTreeWalker(rootElem, NodeFilter.SHOW_TEXT);

  let currentNode: Node | null;
  while ((currentNode = walker.nextNode())) {
    if (currentNode === node) {
      break;
    }
    nodeOffset += currentNode.textContent?.length || 0;
  }

  return nodeOffset + offset;
}

export function mapDOMSelectionToMarkdown(range: Range, markdownSource: string): MarkdownSelection | null {
  const selectedText = range.toString().trim();

  if (!selectedText) {
    return null;
  }

  const { startContainer, endContainer, startOffset, endOffset } = range;

  const isSingleNodeSelection = startContainer === endContainer;

  // Find positioned ancestors
  const startInfo = findNearestElementWithPosition(startContainer);
  const endInfo = findNearestElementWithPosition(endContainer);

  const isSinglePositionElementSelection = startInfo?.element === endInfo?.element;

  if (!startInfo || !endInfo) {
    throw new Error('Could not find source position attributes for selection');
  }

  const nodeStartOffset = getNodeOffsetWithin(startInfo.element, startContainer, startOffset);
  const nodeEndOffset = getNodeOffsetWithin(endInfo.element, endContainer, endOffset);

  // Map to markdown positions
  let startIndex = startInfo.start + nodeStartOffset;
  const markdownRegionText = markdownSource.slice(startIndex);
  const startSearchContent = startContainer.textContent?.slice(
    startOffset,
    isSingleNodeSelection ? endOffset : undefined,
  );
  const startIndexInRegion = markdownRegionText.indexOf(startSearchContent ?? '');
  if (startIndexInRegion !== -1) {
    startIndex += startIndexInRegion;
  }

  let endIndex = endInfo.start + nodeEndOffset + (isSinglePositionElementSelection ? startIndexInRegion : 0);
  const endSearchContent = endContainer.textContent?.slice(isSingleNodeSelection ? startOffset : 0, endOffset);

  // Search for the end content in the markdown to adjust for syntax shifts
  if (endSearchContent) {
    let endIndexOfRegion = endInfo.end;

    // Search the rest of the markdown for endSearchContent, if found adjust endIndexOfRegion to eliminate subsequent matches
    const markdownEndRestRegionText = markdownSource.slice(endIndex, endInfo.end);
    const endIndexInRestRegion = markdownEndRestRegionText.indexOf(endSearchContent);

    if (endIndexInRestRegion !== -1) {
      endIndexOfRegion = endIndex + endIndexInRestRegion;
    }

    const markdownEndRegionText = markdownSource.slice(startIndex, endIndexOfRegion);
    const endIndexInRegion = markdownEndRegionText.lastIndexOf(endSearchContent);

    if (endIndexInRegion !== -1) {
      endIndex = startIndex + endIndexInRegion + endSearchContent.length;
    }
  }

  const result = {
    startIndex,
    endIndex,
    content: selectedText,
  };

  return result;
}
