/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Client } from 'acp-sdk';

import { API_URL } from '#utils/constants.ts';

export const acp = new Client({
  baseUrl: `${API_URL ?? ''}/api/v1/acp/`,
});
