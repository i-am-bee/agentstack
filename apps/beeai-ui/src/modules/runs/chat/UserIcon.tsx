/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { User } from '@carbon/icons-react';

import classes from './UserIcon.module.scss';

export function UserIcon() {
  return (
    <div className={classes.root}>
      <User />
    </div>
  );
}
