/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

export async function transformAgentManifestBody(response: Response, apiPath: string[]) {
  try {
    const body = await response.json();
    const providerId = apiPath.at(2);

    const modifiedBody = { ...body, url: getBaseUrl(`/api/v1/a2a/${providerId}`, true) };

    return JSON.stringify(modifiedBody);
  } catch (err) {
    throw new Error('There was an error transforming agent manifest file.', err);
  }
}
