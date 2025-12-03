/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Code, Root } from 'mdast';
import { visit } from 'unist-util-visit';

/**
 * Remark plugin that adds a mermaidIndex attribute to mermaid code blocks
 * so they can be uniquely identified in the rendered output
 */
export function remarkMermaidIndex() {
  return (tree: Root) => {
    let mermaidIndex = 0;

    visit(tree, 'code', (node: Code) => {
      if (node.lang === 'mermaid') {
        node.data = node.data || {};
        node.data.hProperties = node.data.hProperties || {};
        node.data.hProperties.mermaidIndex = mermaidIndex;
        mermaidIndex++;
      }
    });
  };
}
