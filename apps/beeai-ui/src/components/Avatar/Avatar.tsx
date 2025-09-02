/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import { useSession } from 'next-auth/react';

import classes from './Avatar.module.scss';
import UserAvatar from './UserAvatar';

export default function Avatar() {
  const { data: session } = useSession();
  return (
    <div className={classes.avatar}>
      <OverflowMenu flipped renderIcon={UserAvatar}>
        <OverflowMenuItem itemText={session?.user?.name || 'Not logged in'} />
      </OverflowMenu>
    </div>
  );
}
