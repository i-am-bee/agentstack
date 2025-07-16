/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';
import { ComponentType, useMemo } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { ViewHeader } from '#components/ViewHeader/ViewHeader.tsx';
import { ViewStack } from '#components/ViewStack/ViewStack.tsx';
import { useAppConfig } from '#contexts/AppConfig/index.ts';
import { ProvidersView } from '#modules/providers/components/ProvidersView.tsx';
import { VariablesView } from '#modules/variables/components/VariablesView.tsx';
import { FeatureName } from '#utils/feature-flags.ts';

import { ThemeView } from './ThemeView';

export function SettingsView() {
  const { featureFlags } = useAppConfig();

  const items = useMemo(
    () => ITEMS.filter(({ featureName }) => !featureName || featureFlags[featureName]),
    [featureFlags],
  );

  return (
    <MainContent>
      <Container size="lg">
        <ViewStack>
          <ViewHeader heading="Settings" />
          <Tabs>
            <TabList>
              {items.map(({ title }) => (
                <Tab key={title}>{title}</Tab>
              ))}
            </TabList>
            <TabPanels>
              {items.map(({ title, component: Component }) => (
                <TabPanel key={title}>
                  <Component />
                </TabPanel>
              ))}
            </TabPanels>
          </Tabs>
        </ViewStack>
      </Container>
    </MainContent>
  );
}

const ITEMS: { title: string; component: ComponentType; featureName?: FeatureName }[] = [
  { title: 'Variables', component: VariablesView, featureName: 'Variables' },
  { title: 'Agent providers', component: ProvidersView, featureName: 'Providers' },
  { title: 'Theme', component: ThemeView },
];
