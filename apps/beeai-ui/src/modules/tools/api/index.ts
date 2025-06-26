/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Tool } from './types';

// TODO: The API does not yet support tools, so this is just to suppress TypeScript errors.
export async function listTools() {
  return {
    tools: [{ name: 'search' }, { name: 'wikipedia' }, { name: 'weather' }] as Tool[],
  };
}
