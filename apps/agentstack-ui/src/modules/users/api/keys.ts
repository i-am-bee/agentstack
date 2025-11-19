/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const userKeys = {
  all: () => ['users'] as const,
  detail: () => [...userKeys.all(), 'detail'] as const,
};
