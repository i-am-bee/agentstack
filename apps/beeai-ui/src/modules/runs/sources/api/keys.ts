/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SourceReference } from './types';

export const sourceKeys = {
  all: () => ['sources'] as const,
  details: () => [...sourceKeys.all(), 'detail'] as const,
  detail: ({ source }: { source: SourceReference }) => [...sourceKeys.details(), { source }] as const,
};
