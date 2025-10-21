/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FlatCompat } from '@eslint/eslintrc';
import eslint from '@eslint/js';
import { defineConfig } from 'eslint/config';
import eslintConfigPrettier from 'eslint-config-prettier/flat';
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import typescriptEslint from 'typescript-eslint';

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

/** @type {import('eslint').Linter.Config[]} */
const base = [
  {
    ignores: ['node_modules/**', '.next/**', 'out/**', 'build/**', 'next-env.d.ts', 'dist/**'],
  },
  {
    rules: {
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-import-type-side-effects': 'error',
      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',
    },
  },
];

/** @type {import('eslint').Linter.Config[]} */
const config = [
  ...base,
  eslint.configs.recommended,
  typescriptEslint.configs.recommended,
  eslintConfigPrettier,
  {
    plugins: { 'simple-import-sort': simpleImportSort },
  },
];

/** @type {import('eslint').Linter.Config[]} */
const nextConfig = [
  ...base,
  ...compat.extends('next/core-web-vitals', 'next/typescript', 'prettier'),
  ...compat.plugins('simple-import-sort'),
];

export { nextConfig };

export default defineConfig(config);
