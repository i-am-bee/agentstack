/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const genericApprovalRequestSchema = z.object({
  action: z.literal('generic'),
  title: z.string().nullish().describe('A human-readable title for the action being approved.'),
  description: z.string().nullish().describe('A human-readable description of the action being approved.'),
});

export const toolCallApprovalRequestSchema = z.object({
  action: z.literal('tool-call'),
  title: z.string().nullish().describe('A human-readable title for the tool call being approved.'),
  description: z.string().nullish().describe('A human-readable description of the tool call being approved.'),
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

export const approvalRequestSchema = z.discriminatedUnion('action', [
  genericApprovalRequestSchema,
  toolCallApprovalRequestSchema,
]);

export const approvalResultSchema = z.object({
  decision: z.enum(['approve', 'reject']),
});
