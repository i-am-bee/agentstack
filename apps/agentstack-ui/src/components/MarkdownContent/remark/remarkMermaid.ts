/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Root } from 'hast';
import type { Code } from 'mdast';
import { visit } from 'unist-util-visit';

export function remarkMermaid() {
  return (tree: Root) => {
    visit(tree, 'code', (node: Code) => {
      if (node.lang === 'mermaid') {
        node.data = {
          ...node.data,
          hName: 'mermaidDiagram',
        };
      }
    });
  };
}
