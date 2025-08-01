/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSearchParams } from 'next/navigation';

export function useAgentNameFromPath() {
  const searchParams = useSearchParams();
  const agentName = searchParams.get('agent');

  return agentName ? decodeURIComponent(agentName) : null;
}
