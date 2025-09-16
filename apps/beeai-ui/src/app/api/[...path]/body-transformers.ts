/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCard } from '@a2a-js/sdk';

import { createProxyUrl } from '#utils/api/getProxyUrl.ts';

export async function transformAgentManifestBody(response: Response) {
  try {
    const body: AgentCard = await response.json();

    const modifiedBody = {
      ...body,
      additionalInterfaces: body.additionalInterfaces?.map((item) => ({
        ...item,
        url: createProxyUrl(item.url),
      })),
      url: createProxyUrl(body.url),
    };

    return JSON.stringify(modifiedBody);
  } catch (err) {
    throw new Error('There was an error transforming agent manifest file.', err);
  }
}
