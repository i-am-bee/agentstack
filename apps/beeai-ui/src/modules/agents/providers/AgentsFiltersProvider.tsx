/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import type { PropsWithChildren } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

export interface AgentsFiltersParams {
  search: string;
  frameworks: string[];
  programmingLanguages: string[];
  licenses: string[];
}

export function AgentsFiltersProvider({ children }: PropsWithChildren) {
  const form = useForm<AgentsFiltersParams>({
    mode: 'onBlur',
    defaultValues: {
      search: '',
      frameworks: [],
      programmingLanguages: [],
      licenses: [],
    },
  });

  return <FormProvider {...form}>{children}</FormProvider>;
}
