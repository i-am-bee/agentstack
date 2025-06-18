/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { Root } from 'hast';
import type { Link } from 'mdast';
import { visit } from 'unist-util-visit';

import { CITATION_LINK_PREFIX } from '#modules/runs/sources/constants.ts';
import type { CitationLinkProperties } from '#modules/runs/sources/types.ts';

export function remarkCitationLink() {
  return (tree: Root) => {
    visit(tree, 'link', (node: Link) => {
      const { url } = node;

      if (url.startsWith(CITATION_LINK_PREFIX)) {
        const keys = url.slice(CITATION_LINK_PREFIX.length).split(',');

        node.data = {
          ...node.data,
          hName: 'citationLink',
          hProperties: {
            keys,
          } satisfies CitationLinkProperties,
        };
      }
    });
  };
}
