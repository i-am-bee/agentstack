/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Client } from 'acp-sdk';

import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

export const acp = new Client({
  baseUrl: getBaseUrl('/api/v1/acp/'),
});
