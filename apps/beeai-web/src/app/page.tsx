/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '@/layouts/MainContent';
import { Framework } from '@/modules/home/Framework';
import { Introduction } from '@/modules/home/Introduction';
import { Platform } from '@/modules/home/Platform';

export default function Home() {
  return (
    <MainContent>
      <Introduction />
      <Framework />
      <Platform />
    </MainContent>
  );
}
