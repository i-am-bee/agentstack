/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Add } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { AppHeader } from '#components/layouts/AppHeader.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { ImportAgentsModal } from '#modules/agents/components/import/ImportAgentsModal.tsx';

import classes from './HomeHeader.module.scss';

export function HomeHeader() {
  const { openModal } = useModal();

  return (
    <AppHeader>
      <div className={classes.root}>
        <Button renderIcon={Add} size="sm" onClick={() => openModal((props) => <ImportAgentsModal {...props} />)}>
          Add new agent
        </Button>
      </div>
    </AppHeader>
  );
}
