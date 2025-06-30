/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { promises as fs } from 'node:fs';
import { dirname, extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Loads a file relative to the calling module.
 * - Parses `.json` files as JSON
 * - Returns string content for all other file types
 * Returns `undefined` on read or parse failure.
 *
 * @param relativeTo - Typically `import.meta.url` from the caller module
 * @param filename - File name to load (e.g. 'nav.json' or 'README.md')
 * @returns Parsed object (for JSON) or raw string (for text), or `undefined` on failure
 */
export async function loadFile(relativeTo: string, filename: string): Promise<unknown | string | undefined> {
  const dir = dirname(fileURLToPath(relativeTo));
  const fullPath = join(dir, filename);

  try {
    const content = await fs.readFile(fullPath, 'utf8');
    return extname(filename) === '.json' ? JSON.parse(content) : content;
  } catch {
    return undefined;
  }
}
