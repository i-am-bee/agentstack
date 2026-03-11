/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

/** @type {import('stylelint').Config} */
const config = {
  extends: [
    'stylelint-config-recommended-scss',
    'stylelint-config-css-modules',
    'stylelint-plugin-logical-css/configs/recommended',
  ],
  // Resolve plugin from this shared config package, not the consumer cwd.
  plugins: [require.resolve('stylelint-plugin-logical-css')],
  rules: {
    'scss/function-no-unknown': null,
    'scss/operator-no-newline-after': null,
    'no-descending-specificity': null,
    'nesting-selector-no-missing-scoping-root': null,
    'logical-css/require-logical-units': null,
  },
};

export default config;
