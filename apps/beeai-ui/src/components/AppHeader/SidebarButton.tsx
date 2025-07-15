/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Menu } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';

import { useApp } from '#contexts/App/index.ts';
import { NAV_ITEMS } from '#utils/constants.ts';

import { AppName } from './AppName';
import classes from './SidebarButton.module.scss';

export function SidebarButton() {
  const { setNavigationOpen } = useApp();

  return (
    <div className={clsx(classes.root, { [classes.hasNav]: NAV_ITEMS.length > 0 })}>
      <IconButton
        kind="ghost"
        size="sm"
        wrapperClasses={classes.button}
        onClick={() => setNavigationOpen((value) => !value)}
        label="Toggle sidebar"
        autoAlign
      >
        <Menu />
      </IconButton>

      <AppName />
    </div>
  );
}
