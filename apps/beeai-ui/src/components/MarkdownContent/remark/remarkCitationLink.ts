/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Root } from 'hast';
import type { Link } from 'mdast';
import { visit } from 'unist-util-visit';

import { CITATION_LINK_PREFIX } from '#modules/sources/types.ts';

import type { CitationLinkBaseProps } from '../components/CitationLink/CitationLink';

export function remarkCitationLink() {
  return (tree: Root) => {
    visit(tree, 'link', (node: Link) => {
      const { url } = node;

      if (url.startsWith(CITATION_LINK_PREFIX)) {
        const items = url.slice(CITATION_LINK_PREFIX.length).split(',');

        node.data = {
          ...node.data,
          hName: 'citationLink',
          hProperties: {
            items,
          } satisfies CitationLinkBaseProps,
        };
      }
    });
  };
}
