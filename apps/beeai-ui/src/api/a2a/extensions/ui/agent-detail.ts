/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AUiExtension } from 'beeai-sdk';
import { z } from 'zod';

import { InteractionMode } from '#modules/agents/api/types.ts';

const URI = 'https://a2a-extensions.beeai.dev/ui/agent-detail/v1';

const contributorSchema = z.object({
  name: z.string(),
  email: z.email().nullable(),
  url: z.url().nullable(),
});

const toolSchema = z.object({
  name: z.string(),
  description: z.string(),
});

const schema = z
  .object({
    interaction_mode: z.union([z.enum(InteractionMode), z.string()]).nullable(),
    user_greeting: z.string().nullable(),
    input_placeholder: z.string().nullable(),
    tools: z.array(toolSchema).nullable(),
    framework: z.string().nullable(),
    license: z.string().nullable(),
    programming_language: z.string().nullable(),
    homepage_url: z.url().nullable(),
    source_code_url: z.url().nullable(),
    container_image_url: z.url().nullable(),
    author: contributorSchema.nullable(),
    contributors: z.array(contributorSchema).nullable(),
  })
  .partial();

export type AgentDetailTool = z.infer<typeof toolSchema>;
export type AgentDetailContributor = z.infer<typeof contributorSchema>;

export type AgentDetail = z.infer<typeof schema>;

export const agentDetailExtension: A2AUiExtension<typeof URI, AgentDetail> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};
