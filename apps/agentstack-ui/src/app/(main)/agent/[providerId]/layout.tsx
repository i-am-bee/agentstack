/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Metadata } from 'next';

import { metadata } from '#app/layout.tsx';
import { AppLayout } from '#components/layouts/AppLayout.tsx';
import { HeaderLayout } from '#components/layouts/HeaderLayout.tsx';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { AgentHeader } from '#modules/agents/components/detail/AgentHeader.tsx';

import { fetchAgent } from './rsc';

interface Props {
  params: Promise<{
    providerId: string;
  }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { providerId } = await params;

  try {
    const agent = await fetchAgent(providerId);
    if (agent) {
      return {
        ...metadata,
        title: `${agent.name} | ${runtimeConfig.appName}`,
      };
    }
  } catch (error) {
    console.error(`Failed to fetch agent for providerId ${providerId} while generating metadata:`, error);
  }

  return metadata;
}

export default function RunLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AppLayout>
      <HeaderLayout>
        <AgentHeader />

        {children}
      </HeaderLayout>
    </AppLayout>
  );
}
