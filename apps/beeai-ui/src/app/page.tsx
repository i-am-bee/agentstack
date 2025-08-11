/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';
import { connection } from 'next/server';

import { auth } from '#auth.ts';
import EntityNotFound from '#components/EntityNotFound/EntityNotFound.tsx';
import { ErrorPage } from '#components/ErrorPage/ErrorPage.tsx';
import { buildAgent, isAgentUiSupported, sortAgentsByName } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { routes } from '#utils/router.ts';
// Prevent static render, the API is not available at build time
export const dynamic = 'force-dynamic';

export default async function LandingPage() {
  let firstAgentName;
  const session = await auth();
  const isOidcDisabled = process.env.NEXT__DISABLE_OIDC === 'true';
  if (!session?.user) {
    await connection();
    // only force login if oidc is enabled.
    if (!isOidcDisabled) {
      redirect(routes.login());
    }
  }

  try {
    const response = await listProviders();

    const agents = response?.items?.map(buildAgent).filter(isAgentUiSupported).sort(sortAgentsByName);

    firstAgentName = agents?.at(0)?.name;
  } catch (err) {
    console.log(err);

    // TODO: Process 503 Service unavailable
    return <ErrorPage message={'There was an error loading agents.'} />;
  }

  if (firstAgentName) {
    redirect(routes.agentRun({ name: firstAgentName }));
  }

  return <EntityNotFound type="agent" message="No agents with supported UI found." showBackHomeButton={false} />;
}
