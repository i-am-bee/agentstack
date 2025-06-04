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

import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { fileURLToPath } from 'node:url';

/**
 * Dynamically loads a JSON file relative to the caller module.
 * Works in ESM environments using import assertions.
 *
 * @param relativeTo - Typically `import.meta.url` from the caller module
 * @param filename - The JSON file name to load (e.g. 'nav.json')
 * @returns Parsed JSON object, or `undefined` if loading/parsing fails
 */
export async function loadJson(relativeTo: string, filename: string) {
  const dir = dirname(fileURLToPath(relativeTo));
  const fullPath = join(dir, filename);
  const filePath = pathToFileURL(fullPath).href;

  try {
    const module = await import(filePath, {
      with: { type: 'json' },
    });
    return module.default;
  } catch {
    return undefined;
  }
}
