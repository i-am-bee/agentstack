/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';

import EntityNotFound from '#components/EntityNotFound/EntityNotFound.tsx';
import { listAgents } from '#modules/agents/api/index.ts';
import { isAgentUiSupported, sortAgentsByName } from '#modules/agents/utils.ts';
import { routes } from '#utils/router.ts';

export default async function LandingPage() {
  let firstAgentName;

  try {
    const response = await listAgents();
    const agents = response?.filter(isAgentUiSupported).sort(sortAgentsByName);

    firstAgentName = agents?.at(0)?.name;
  } catch (err) {
    console.log(err);
  }

  if (firstAgentName) {
    redirect(routes.agentRun({ name: firstAgentName }));
  }

  return <EntityNotFound type="agent" message="No agents with supported UI found." showBackHomeButton={false} />;
}
