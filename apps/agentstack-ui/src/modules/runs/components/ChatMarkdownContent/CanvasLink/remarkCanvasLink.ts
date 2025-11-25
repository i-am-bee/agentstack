/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Root } from 'hast';
import type { Link } from 'mdast';
import { visit } from 'unist-util-visit';

import type { MessageCanvasCardProps } from '#modules/canvas/components/MessageCanvasCard.tsx';

export const ARTIFACT_LINK_PREFIX = 'artifact:';

export function remarkCanvasLink() {
  return (tree: Root) => {
    visit(tree, 'link', (node: Link) => {
      const { url, children } = node;

      if (url.startsWith(ARTIFACT_LINK_PREFIX)) {
        const artifactId = url.slice(ARTIFACT_LINK_PREFIX.length);
        const firstChild = children.at(0);
        const name = firstChild?.type === 'text' ? firstChild.value : '';

        node.data = {
          ...node.data,
          hName: 'canvasLink',
          hProperties: {
            name,
            artifactId,
          } satisfies MessageCanvasCardProps,
        };
      }
    });
  };
}
