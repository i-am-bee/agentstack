/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/interactions/approval/v1';

export const approvalRequestSchema = z.object({
  title: z.string().nullish().describe('A human-readable title for the action being approved.'),
  description: z.string().nullish().describe('A human-readable description of the action that is being approved.'),
});
export type ApprovalRequest = z.infer<typeof approvalRequestSchema>;

export const toolCallApprovalRequestSchema = approvalRequestSchema.extend({
  name: z.string().describe('The programmatic name of the tool.'),
  input: z.object().nullish().describe('The input for the tool.'),
  server: z
    .object({
      name: z.string().describe('The programmatic name of the server.'),
      title: z.string().nullish().describe('A human-readable title for the server.'),
      version: z.string().describe('The version of the server.'),
    })
    .nullish()
    .describe('The server executing the tool.'),
});
export type ToolCallApprovalRequest = z.infer<typeof toolCallApprovalRequestSchema>;

export const approvalResultSchema = z.object({
  action: z.enum(['approve', 'reject']),
});
export type ApprovalResult = z.infer<typeof approvalResultSchema>;

export const approvalExtension: A2AUiExtension<typeof URI, ApprovalRequest> = {
  getMessageMetadataSchema: () => z.object({ [URI]: approvalRequestSchema }).partial(),
  getUri: () => URI,
};
