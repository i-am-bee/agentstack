/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useProvider } from '#modules/providers/api/queries/useProvider.ts';

import type { Agent } from '../api/types';

interface Props {
  agent?: Agent;
}

export function useMissingEnvs({ agent }: Props) {
  const { data, isPending } = useProvider({ id: agent?.provider?.id });
  const missingEnvs = data?.missing_configuration ?? [];

  return { missingEnvs, isPending };
}
