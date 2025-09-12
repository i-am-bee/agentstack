/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Program } from 'estree';
import { valueToEstree } from 'estree-util-value-to-estree';
import type { VFile } from 'vfile';

export function recmaExportToc() {
  return (tree: Program, file: VFile) => {
    const toc = file.data.toc ?? [];

    tree.body.push({
      type: 'ExportNamedDeclaration',
      declaration: {
        type: 'VariableDeclaration',
        kind: 'const',
        declarations: [
          {
            type: 'VariableDeclarator',
            id: { type: 'Identifier', name: 'toc' },
            init: valueToEstree(toc),
          },
        ],
      },
      specifiers: [],
      attributes: [],
      source: null,
    });
  };
}
