/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/interactions/approval/v1';

const schema = z.object({
  title: z.string().nullable().describe('A human-readable title for the action being approved.'),
  description: z.string().nullable().describe('A human-readable description of the action that is being approved.'),
});

export type ApprovalRequest = z.infer<typeof schema>;

export const approvalExtension: A2AUiExtension<typeof URI, ApprovalRequest> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};
