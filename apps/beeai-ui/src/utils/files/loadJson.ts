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
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Loads and parses a JSON file relative to the calling module.
 * Returns undefined if the file is missing or contains invalid JSON.
 *
 * @param relativeTo - Typically `import.meta.url` from the caller module
 * @param filename - The JSON file name to load (e.g. 'nav.json')
 * @returns Parsed JSON object, or `undefined` if loading/parsing fails
 */
export async function loadJson(relativeTo: string, filename: string) {
  const dir = dirname(fileURLToPath(relativeTo));
  const fullPath = join(dir, filename);

  try {
    const content = await fs.readFile(fullPath, 'utf8');
    return JSON.parse(content);
  } catch {
    return undefined;
  }
}
