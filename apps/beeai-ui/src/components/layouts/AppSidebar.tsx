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

import { AgentsNav } from '#components/AgentsNav/AgentsNav.tsx';
import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { UserNav } from '#components/UserNav/UserNav.tsx';
import { useApp } from '#contexts/App/index.ts';
import { useAppConfig } from '#contexts/AppConfig/index.ts';

import classes from './AppSidebar.module.scss';

export function AppSidebar() {
  const { navigationOpen, navigationPanelRef } = useApp();
  const { featureFlags } = useAppConfig();

  return (
    <SidePanel variant="left" isOpen={navigationOpen} ref={navigationPanelRef}>
      <div className={classes.root}>
        <AgentsNav />

        {featureFlags?.user_navigation && (
          <div className={classes.footer}>
            <UserNav />
          </div>
        )}
      </div>
    </SidePanel>
  );
}
