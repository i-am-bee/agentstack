/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Menu, RightPanelClose, RightPanelOpen } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { useApp } from '#contexts/App/index.ts';

import classes from './SidebarButton.module.scss';

export function SidebarButton() {
  const {
    config: { appName },
    sidebarOpen,
    setSidebarOpen,
  } = useApp();

  return (
    <Button className={classes.root} kind="ghost" size="sm" onClick={() => setSidebarOpen((state) => !state)}>
      <div className={classes.icon}>
        <Menu />

        {sidebarOpen ? <RightPanelOpen /> : <RightPanelClose />}
      </div>

      <span className={classes.label}>{appName}</span>
    </Button>
  );
}
