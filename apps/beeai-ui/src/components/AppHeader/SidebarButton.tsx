/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Menu } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { useApp } from '#contexts/App/index.ts';
import { APP_NAME } from '#utils/vite-constants.ts';

import classes from './SidebarButton.module.scss';

export function SidebarButton() {
  const { setNavigationOpen } = useApp();

  return (
    <div className={classes.root}>
      <IconButton
        kind="ghost"
        size="sm"
        wrapperClasses={classes.button}
        onClick={() => setNavigationOpen?.((value) => !value)}
        label="Toggle sidebar"
        autoAlign
      >
        <Menu />
      </IconButton>

      <span className={classes.label}>{APP_NAME}</span>
    </div>
  );
}
