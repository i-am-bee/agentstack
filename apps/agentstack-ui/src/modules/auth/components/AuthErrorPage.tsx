/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Button, InlineNotification } from '@carbon/react';
import { signOut } from 'next-auth/react';

import { routes } from '#utils/router.ts';

import classes from './AuthErrorPage.module.scss';

export function AuthErrorPage() {
  return (
    <div className={classes.root}>
      <InlineNotification
        kind="error"
        title="Authentication Error"
        subtitle="Server authentication failed. Please try signing in again."
        hideCloseButton
        lowContrast
      />
      <Button kind="primary" onClick={() => signOut({ redirectTo: routes.signIn() })}>
        Sign in again
      </Button>
    </div>
  );
}
