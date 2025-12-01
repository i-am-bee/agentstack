/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Root } from 'hast';
import { visit } from 'unist-util-visit';

export function rehypeSourcePosition() {
  return (tree: Root) => {
    visit(tree, 'element', (node) => {
      const element = node;
      if (node.position?.start?.offset !== undefined && node.position?.end?.offset !== undefined) {
        const existingStart = element.properties[MD_START_INDEX_ATTR];
        const existingEnd = element.properties[MD_END_INDEX_ATTR];

        element.properties[MD_START_INDEX_ATTR] = Math.min(
          Number(existingStart ?? Infinity),
          node.position.start.offset,
        );

        element.properties[MD_END_INDEX_ATTR] = Math.max(Number(existingEnd ?? 0), node.position.end.offset);
      }
    });
  };
}

export const MD_START_INDEX_ATTR = 'data-md-start';
export const MD_END_INDEX_ATTR = 'data-md-end';
