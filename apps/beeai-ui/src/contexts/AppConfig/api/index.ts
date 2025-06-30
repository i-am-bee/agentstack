/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

export async function readConfig() {
  const response = await api.GET('/api/v1/ui/config');
  return ensureData(response);
}
