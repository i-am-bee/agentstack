/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useParams } from 'next/navigation';

export function useAgentNameFromPath() {
  const params = useParams();

  return params?.agentName ? params.agentName.toString() : null;
}
