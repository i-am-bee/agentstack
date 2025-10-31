/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Add } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { AppName } from '#components/AppName/AppName.tsx';
import { AppHeader } from '#components/layouts/AppHeader.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { ImportAgentsModal } from '#modules/agents/components/import/ImportAgentsModal.tsx';

import classes from './CommonHeader.module.scss';

export function CommonHeader() {
  const { openModal } = useModal();

  return (
    <AppHeader>
      <div className={classes.root}>
        <AppName />

        <div className={classes.right}>
          <Button renderIcon={Add} size="sm" onClick={() => openModal((props) => <ImportAgentsModal {...props} />)}>
            Add new agent
          </Button>
        </div>
      </div>
    </AppHeader>
  );
}
