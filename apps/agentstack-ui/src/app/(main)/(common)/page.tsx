/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { HomeView } from '#modules/home/components/HomeView.tsx';

// The homepage fetches data via the server API client which reads request headers,
// so force a dynamic render to avoid static generation errors.
export const dynamic = 'force-dynamic';

export default async function HomePage() {
  return <HomeView />;
}
