/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

declare module '@i-am-bee/eslint-config' {
  import type { Linter } from 'eslint';

  const config: Linter.Config[];
  const nextConfig: Linter.Config[];

  export { nextConfig };
  export default config;
}
