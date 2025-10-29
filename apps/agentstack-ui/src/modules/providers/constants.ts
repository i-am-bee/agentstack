/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ProviderSource } from './types';

export const ProviderSourcePrefixes = {
  [ProviderSource.GitHub]: 'git+',
  [ProviderSource.Docker]: '',
} as const;
