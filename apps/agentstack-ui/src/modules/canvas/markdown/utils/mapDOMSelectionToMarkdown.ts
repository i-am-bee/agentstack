/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  MD_POSITION_END_ATTR,
  MD_POSITION_START_ATTR,
} from '#components/MarkdownContent/rehype/rehypeSourcePosition.ts';

export interface MarkdownSelection {
  /** Start offset in the markdown source string */
  start: number;
  /** End offset in the markdown source string */
  end: number;
  /** The selected text from the rendered output */
  text: string;
}

export function mapDOMSelectionToMarkdown(range: Range, markdownSource: string): MarkdownSelection | null {
  try {
    const selectedText = range.toString().trim();

    if (!selectedText) {
      return null;
    }

    const firtElementStart: number = parseInt(
      range.startContainer.parentElement?.getAttribute(MD_POSITION_START_ATTR) ?? '',
    );
    let start = firtElementStart + range.startOffset;

    const lastElementEnd: number = parseInt(range.endContainer.parentElement?.getAttribute(MD_POSITION_END_ATTR) ?? '');
    const offsetEndAdjustment = (range.endContainer.textContent?.length ?? 0) - range.endOffset;
    const end = lastElementEnd - offsetEndAdjustment;

    const regionText = markdownSource.slice(start, end);
    const trimmedSelection = selectedText.trim();

    const { startContainer, endContainer } = range;
    const isSingleNodeSelection = startContainer === endContainer;

    // Fine-tune start position within the region, it can be shifted by markdown syntax of the current node that is not included in selection
    const startSearchContent = range.startContainer.textContent?.slice(
      range.startOffset,
      isSingleNodeSelection ? range.endOffset : undefined,
    );
    const indexInRegion = regionText.indexOf(startSearchContent ?? '');
    if (indexInRegion !== -1) {
      start += indexInRegion;
    }

    // console.log({ lastElementEnd, endOffset: range.endOffset, offsetEndAdjustment });

    const result = {
      start,
      end,
      text: trimmedSelection,
    };

    return result;
  } catch (error) {
    console.error('Error mapping selection to markdown:', error);
    return null;
  }
}
