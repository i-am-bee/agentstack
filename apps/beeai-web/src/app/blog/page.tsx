/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { APP_NAME } from '@i-am-bee/beeai-ui';
import type { Metadata } from 'next';

import { MainContentView } from '@/layouts/MainContentView';
import { BlogView } from '@/modules/blog/components/BlogView';

export default function Blog() {
  return (
    <MainContentView spacing={false}>
      <BlogView />
    </MainContentView>
  );
}

export const metadata: Metadata = {
  title: `Blog | ${APP_NAME}`,
};
