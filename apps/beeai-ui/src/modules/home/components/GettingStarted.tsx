/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { INSTALL_BEEAI } from '@i-am-bee/beeai-ui';

import { CopySnippet } from '#components/CopySnippet/CopySnippet.tsx';
import { Container } from '#components/layouts/Container.tsx';

import classes from './GettingStarted.module.scss';
import { GitHubButton } from './GitHubButton';
import { LogoBeeAI } from './LogoBeeAI';

export function GettingStarted() {
  return (
    <div className={classes.root}>
      <Container size="xs">
        <LogoBeeAI />

        <p className={classes.description}>
          The open-source platform to discover and run AI&nbsp;agents from&nbsp;any&nbsp;framework
        </p>

        <div className={classes.bottom}>
          <CopySnippet>{INSTALL_BEEAI}</CopySnippet>
          <GitHubButton />
        </div>
      </Container>
    </div>
  );
}
