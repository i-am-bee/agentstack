/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { agentDetailSchema } from './schemas';
import type { AgentDetail } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/agent-detail/v1';

export const agentDetailExtension: A2AUiExtension<typeof URI, AgentDetail> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: agentDetailSchema }).partial(),
};
