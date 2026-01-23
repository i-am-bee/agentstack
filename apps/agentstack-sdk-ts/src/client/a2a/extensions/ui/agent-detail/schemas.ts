/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { InteractionMode } from './types';

export const interactionModeSchema = z.enum(InteractionMode);

export const agentDetailToolSchema = z.object({
  name: z.string(),
  description: z.string(),
});

export const agentDetailContributorSchema = z.object({
  name: z.string(),
  email: z.string().nullish(),
  url: z.string().nullish(),
});

export const agentDetailSchema = z.object({
  interaction_mode: z.union([interactionModeSchema, z.string()]).nullish(),
  user_greeting: z.string().nullish(),
  input_placeholder: z.string().nullish(),
  tools: z.array(agentDetailToolSchema).nullish(),
  framework: z.string().nullish(),
  license: z.string().nullish(),
  programming_language: z.string().nullish(),
  homepage_url: z.string().nullish(),
  source_code_url: z.string().nullish(),
  container_image_url: z.string().nullish(),
  author: agentDetailContributorSchema.nullish(),
  contributors: z.array(agentDetailContributorSchema).nullish(),
});
