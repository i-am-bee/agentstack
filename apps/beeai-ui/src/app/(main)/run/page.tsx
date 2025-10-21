/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound, permanentRedirect } from 'next/navigation';

import { routes } from '#utils/router.ts';

interface Props {
  searchParams: Promise<{ p?: string; c?: string }>;
}

export default async function RunRedirectPage({ searchParams }: Props) {
  const { p: providerId, c: contextId } = await searchParams;

  // Handle previous URL structure
  if (providerId) {
    permanentRedirect(routes.agentRun({ providerId, contextId }));
  }

  notFound();
}
