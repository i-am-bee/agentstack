/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

declare module '@i-am-bee/lint-config/eslint' {
  import type { Linter } from 'eslint';

  const config: Linter.Config[];
  const nextConfig: Linter.Config[];

  export { nextConfig };
  export default config;
}

declare module '@i-am-bee/lint-config/prettier' {
  import type { Config } from 'prettier';

  const config: Config;

  export default config;
}

declare module '@i-am-bee/lint-config/stylelint' {
  import type { Config } from 'stylelint';

  const config: Config;

  export default config;
}
