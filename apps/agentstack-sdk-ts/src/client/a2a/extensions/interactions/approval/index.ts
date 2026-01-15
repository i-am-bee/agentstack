/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { approvalRequestSchema, approvalResultSchema } from './schemas';
import type { ApprovalRequest, ApprovalResult } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/interactions/approval/v1';

export const approvalExtension: A2AUiExtension<typeof URI, ApprovalRequest> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: approvalRequestSchema }).partial(),
};

export const approvalResultExtension: A2AUiExtension<typeof URI, ApprovalResult> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: approvalResultSchema }).partial(),
};
