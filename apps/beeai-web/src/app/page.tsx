/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { GettingStarted } from '@i-am-bee/beeai-ui';

import { MainContent } from '@/layouts/MainContent';
import { ExperienceShowcase } from '@/modules/home/ExperienceShowcase';

export default function Home() {
  return (
    <MainContent>
      <GettingStarted />

      <ExperienceShowcase />
    </MainContent>
  );
}
