/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { Add } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { AppName } from '#components/AppName/AppName.tsx';
import { AppHeader } from '#components/layouts/AppHeader.tsx';
import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { ImportAgentsModal } from '#modules/agents/components/import/ImportAgentsModal.tsx';
import { useUser } from '#modules/users/api/queries/useUser.ts';

import classes from './CommonHeader.module.scss';

export function CommonHeader() {
  const { openModal } = useModal();
  const { data: user } = useUser();

  const isAdmin = user?.role === 'admin';

  const addNewAgentButton = (
    <Button
      renderIcon={Add}
      size="sm"
      disabled={!isAdmin}
      onClick={() => openModal((props) => <ImportAgentsModal {...props} />)}
    >
      Add new agent
    </Button>
  );

  return (
    <AppHeader>
      <div className={classes.root}>
        <AppName />

        <div className={classes.right}>
          {isAdmin ? (
            addNewAgentButton
          ) : (
            <Tooltip content="Adding agents requires elevated permissions." asChild placement="bottom-end">
              {addNewAgentButton}
            </Tooltip>
          )}
        </div>
      </div>
    </AppHeader>
  );
}
