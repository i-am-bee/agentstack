/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/** @type {import('stylelint').Config} */
const config = {
  extends: ['stylelint-config-recommended-scss', 'stylelint-config-css-modules'],
  plugins: ['stylelint-plugin-logical-css'],
  rules: {
    'scss/function-no-unknown': null,
    'scss/operator-no-newline-after': null,
    'no-descending-specificity': null,
    'plugin/use-logical-properties-and-values': [
      true,
      {
        severity: 'warning',
        ignore: ['overflow-y', 'overflow-x', '-webkit-box-orient'],
      },
    ],
    'nesting-selector-no-missing-scoping-root': null,
  },
};

export default config;