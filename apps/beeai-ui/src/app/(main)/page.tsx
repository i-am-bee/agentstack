/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';

import EntityNotFound from '#components/EntityNotFound/EntityNotFound.tsx';
import { ErrorPage } from '#components/ErrorPage/ErrorPage.tsx';
import { buildAgent, isAgentUiSupported, sortAgentsByName } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { routes } from '#utils/router.ts';

// Prevent static render, the API is not available at build time
export const dynamic = 'force-dynamic';

export default async function LandingPage() {
  let firstAgentProviderId;

  try {
    const response = await listProviders();

    const agents = response?.items?.map(buildAgent).filter(isAgentUiSupported).sort(sortAgentsByName);

    firstAgentProviderId = agents?.at(0)?.provider.id;
  } catch (err) {
    console.log(err);

    // TODO: Process 503 Service unavailable
    return <ErrorPage message={'There was an error loading agents.'} />;
  }

  if (firstAgentProviderId) {
    redirect(routes.agentRun({ providerId: firstAgentProviderId }));
  }

  return <EntityNotFound type="agent" message="No agents with supported UI found." showBackHomeButton={false} />;
}
