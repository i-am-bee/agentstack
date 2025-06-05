/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AgentRun } from '#modules/runs/components/AgentRun.tsx';

interface Props {
  params: Promise<{ name: string }>;
}

export default async function AgentRunPage({ params }: Props) {
  const { name } = await params;
  return <AgentRun name={name} />;
}
