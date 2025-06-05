/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound, redirect } from 'next/navigation';

import { listAgents } from '#modules/agents/api/index.ts';
import { routes } from '#utils/router.ts';

export default async function LandingPage() {
  try {
    const response = await listAgents();
    const firstAgentName = response?.agents.at(0)?.name;

    if (firstAgentName) {
      redirect(routes.agentRun({ name: firstAgentName }));
    }
  } catch (err) {
    // TODO:
    console.log(err);
  }

  return notFound();
}
