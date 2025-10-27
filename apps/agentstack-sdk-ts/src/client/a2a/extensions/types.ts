/**
 * Copyright 2025 © Agent Stack a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { z } from 'zod';

export interface A2AExtension<U extends string> {
  getUri: () => U;
}

export interface A2AUiExtension<U extends string, D> extends A2AExtension<U> {
  getMessageMetadataSchema: () => z.ZodSchema<Partial<Record<U, D>>>;
}

export interface A2AServiceExtension<U extends string, D, F> extends A2AExtension<U> {
  getUri: () => U;
  getDemandsSchema: () => z.ZodSchema<D>;
  getFulfillmentSchema: () => z.ZodSchema<F>;
}
