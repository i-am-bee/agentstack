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
