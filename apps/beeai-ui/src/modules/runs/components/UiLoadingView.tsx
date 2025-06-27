/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Loading } from '@carbon/react';

import { MainContent } from '#components/layouts/MainContent.tsx';

import classes from './UiLoadingView.module.scss';

export function UiLoadingView() {
  return (
    <MainContent>
      <div className={classes.root}>
        <Loading withOverlay={false} />
      </div>
    </MainContent>
  );
}
