/**
 * Copyright 2025 © Agent Stack a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.dev/ui/trajectory/v1';

const schema = z.object({
  title: z.string().nullish(),
  content: z.string().nullish(),
});

export type TrajectoryMetadata = z.infer<typeof schema>;

export const trajectoryExtension: A2AUiExtension<typeof URI, TrajectoryMetadata> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};
