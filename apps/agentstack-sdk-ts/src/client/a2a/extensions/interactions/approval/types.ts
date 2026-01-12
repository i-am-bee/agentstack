/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  approvalRequestSchema,
  approvalResultSchema,
  genericApprovalRequestSchema,
  toolCallApprovalRequestSchema,
} from './schemas';

export type GenericApprovalRequest = z.infer<typeof genericApprovalRequestSchema>;
export type ToolCallApprovalRequest = z.infer<typeof toolCallApprovalRequestSchema>;

export type ApprovalRequest = z.infer<typeof approvalRequestSchema>;
export type ApprovalResult = z.infer<typeof approvalResultSchema>;
