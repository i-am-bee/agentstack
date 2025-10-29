/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import { interactionModeSchema } from '../../../../types';
import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.dev/ui/agent-detail/v1';

const contributorSchema = z.object({
  name: z.string(),
  email: z.string().nullish(),
  url: z.string().nullish(),
});

const toolSchema = z.object({
  name: z.string(),
  description: z.string(),
});

const schema = z.object({
  interaction_mode: z.union([interactionModeSchema, z.string()]).nullish(),
  user_greeting: z.string().nullish(),
  input_placeholder: z.string().nullish(),
  tools: z.array(toolSchema).nullish(),
  framework: z.string().nullish(),
  license: z.string().nullish(),
  programming_language: z.string().nullish(),
  homepage_url: z.string().nullish(),
  source_code_url: z.string().nullish(),
  container_image_url: z.string().nullish(),
  author: contributorSchema.nullish(),
  contributors: z.array(contributorSchema).nullish(),
});

export type AgentDetailTool = z.infer<typeof toolSchema>;
export type AgentDetailContributor = z.infer<typeof contributorSchema>;
export type AgentDetail = z.infer<typeof schema>;

export const agentDetailExtension: A2AUiExtension<typeof URI, AgentDetail> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};
