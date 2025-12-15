/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { trajectoryMetadataSchema } from './schemas';
import type { TrajectoryMetadata } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/trajectory/v1';

export const trajectoryExtension: A2AUiExtension<typeof URI, TrajectoryMetadata> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: trajectoryMetadataSchema }).partial(),
};
