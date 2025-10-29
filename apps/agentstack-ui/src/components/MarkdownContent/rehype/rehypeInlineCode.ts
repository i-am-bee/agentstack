/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Root } from 'hast';
import { visit } from 'unist-util-visit';

export function rehypeInlineCode() {
  return (tree: Root) => {
    visit(tree, (node, _, parent) => {
      if (
        node.type === 'element' &&
        node.tagName === 'code' &&
        parent?.type === 'element' &&
        parent.tagName !== 'pre'
      ) {
        node.properties.inline = true;
      }
    });
  };
}
