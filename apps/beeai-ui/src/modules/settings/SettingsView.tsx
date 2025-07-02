/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { ViewHeader } from '#components/ViewHeader/ViewHeader.tsx';
import { ViewStack } from '#components/ViewStack/ViewStack.tsx';
import { ProvidersView } from '#modules/providers/components/ProvidersView.tsx';
import { VariablesView } from '#modules/variables/components/VariablesView.tsx';

import { ThemeView } from './ThemeView';

export function SettingsView() {
  return (
    <MainContent>
      <Container size="lg">
        <ViewStack>
          <ViewHeader heading="Settings" />
          <Tabs>
            <TabList>
              <Tab>Variables</Tab>
              <Tab>Agent providers</Tab>
              <Tab>Theme</Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                <VariablesView />{' '}
              </TabPanel>
              <TabPanel>
                <ProvidersView />{' '}
              </TabPanel>
              <TabPanel>
                <ThemeView />{' '}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ViewStack>
      </Container>
    </MainContent>
  );
}
