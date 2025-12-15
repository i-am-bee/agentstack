/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  createModelProviderRequestSchema,
  createModelProviderResponseSchema,
  deleteModelProviderRequestSchema,
  deleteModelProviderResponseSchema,
  listModelProvidersRequestSchema,
  listModelProvidersResponseSchema,
  matchModelProvidersRequestSchema,
  matchModelProvidersResponseSchema,
  modelProviderSchema,
  readModelProviderRequestSchema,
  readModelProviderResponseSchema,
} from './schemas';

export enum ModelCapability {
  Llm = 'llm',
  Embedding = 'embedding',
}

export enum ModelProviderType {
  Anthropic = 'anthropic',
  Cerebras = 'cerebras',
  Chutes = 'chutes',
  Cohere = 'cohere',
  DeepSeek = 'deepseek',
  Gemini = 'gemini',
  GitHub = 'github',
  Groq = 'groq',
  Watsonx = 'watsonx',
  Jan = 'jan',
  Mistral = 'mistral',
  Moonshot = 'moonshot',
  Nvidia = 'nvidia',
  Ollama = 'ollama',
  OpenAI = 'openai',
  OpenRouter = 'openrouter',
  Perplexity = 'perplexity',
  Together = 'together',
  Voyage = 'voyage',
  Rits = 'rits',
  Other = 'other',
}

export type ModelProvider = z.infer<typeof modelProviderSchema>;

export type ListModelProvidersRequest = z.infer<typeof listModelProvidersRequestSchema>;
export type ListModelProvidersResponse = z.infer<typeof listModelProvidersResponseSchema>;

export type CreateModelProviderRequest = z.infer<typeof createModelProviderRequestSchema>;
export type CreateModelProviderResponse = z.infer<typeof createModelProviderResponseSchema>;

export type ReadModelProviderRequest = z.infer<typeof readModelProviderRequestSchema>;
export type ReadModelProviderResponse = z.infer<typeof readModelProviderResponseSchema>;

export type DeleteModelProviderRequest = z.infer<typeof deleteModelProviderRequestSchema>;
export type DeleteModelProviderResponse = z.infer<typeof deleteModelProviderResponseSchema>;

export type MatchModelProvidersRequest = z.infer<typeof matchModelProvidersRequestSchema>;
export type MatchModelProvidersResponse = z.infer<typeof matchModelProvidersResponseSchema>;
