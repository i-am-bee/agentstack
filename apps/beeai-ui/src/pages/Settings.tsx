/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { ViewHeader } from '#components/ViewHeader/ViewHeader.tsx';
import { ViewStack } from '#components/ViewStack/ViewStack.tsx';
import { ProvidersView } from '#modules/providers/components/ProvidersView.tsx';
import { ThemeView } from '#modules/settings/ThemeView.tsx';
import { VariablesView } from '#modules/variables/components/VariablesView.tsx';

export function Settings() {
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
                <VariablesView />
              </TabPanel>

              <TabPanel>
                <ProvidersView />
              </TabPanel>

              <TabPanel>
                <ThemeView />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ViewStack>
      </Container>
    </MainContent>
  );
}
