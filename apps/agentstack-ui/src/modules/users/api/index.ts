/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';

export async function readUser() {
  const response = await agentStackClient.readUser();
  const result = unwrapResult(response);

  return result;
}
