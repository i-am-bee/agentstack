/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const addConnectorFormSchema = z
  .object({
    name: z.string().trim(),
    url: z.url().trim(),
    clientId: z.string().trim().optional(),
    clientSecret: z.string().trim().optional(),
  })
  .refine(
    (data) => {
      if (!data.clientId) {
        return !data.clientSecret;
      }

      return true;
    },
    {
      path: ['clientSecret'],
      error: 'Client secret can only be set when a client ID is provided',
    },
  );

export type AddConnectorForm = z.infer<typeof addConnectorFormSchema>;
