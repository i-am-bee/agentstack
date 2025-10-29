/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { HeaderLayout } from '#components/layouts/HeaderLayout.tsx';
import { HomeHeader } from '#modules/home/components/HomeHeader.tsx';
import { HomeView } from '#modules/home/components/HomeView.tsx';

export default async function HomePage() {
  return (
    <HeaderLayout>
      <HomeHeader />

      <HomeView />
    </HeaderLayout>
  );
}
