/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { defineConfig } from 'tsup';

export default defineConfig([
  {
    entry: {
      index: 'src/index.ts',
      api: 'src/api.ts',
      core: 'src/core.ts',
      extensions: 'src/extensions.ts',
      server: 'src/server.ts',
    },
    format: ['esm', 'cjs'],
    dts: true,
    clean: true,
    splitting: false,
  },
  {
    entry: { index: 'src/index.ts' },
    format: ['iife'],
    outExtension: () => ({ js: '.umd.js' }),
    globalName: 'AgentStackSDK',
  },
]);
