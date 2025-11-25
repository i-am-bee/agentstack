/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Root } from 'hast';
import { visit } from 'unist-util-visit';

export function rehypeSourcePosition() {
  return (tree: Root) => {
    visit(tree, 'text', (node, _index, parent) => {
      if (!node.position?.start?.offset || !node.position?.end?.offset) {
        return;
      }

      if (parent && parent.type === 'element') {
        // Store the text node's position on its parent element
        // If parent already has position data, extend the range
        const existingStart = Number(parent.properties[MD_POSITION_START_ATTR]);
        const existingEnd = Number(parent.properties[MD_POSITION_END_ATTR]);
        parent.properties[MD_POSITION_START_ATTR] =
          existingStart !== undefined
            ? Math.min(existingStart, node.position.start.offset)
            : node.position.start.offset;

        parent.properties[MD_POSITION_END_ATTR] =
          existingEnd !== undefined ? Math.max(existingEnd, node.position.end.offset) : node.position.end.offset;
      }
    });

    // Also process element nodes that have position but no text children
    visit(tree, 'element', (node) => {
      const element = node;
      if (node.position?.start?.offset && node.position?.end?.offset) {
        if (!element.properties[MD_POSITION_START_ATTR]) {
          element.properties[MD_POSITION_START_ATTR] = node.position.start.offset;
          element.properties[MD_POSITION_END_ATTR] = node.position.end.offset;
        }
      }
    });
  };
}

export const MD_POSITION_START_ATTR = 'data-md-start';
export const MD_POSITION_END_ATTR = 'data-md-end';
