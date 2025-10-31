/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSession } from 'next-auth/react';

import { getNameInitials } from '#utils/helpers.ts';

import classes from './UserAvatar.module.scss';

export default function UserAvatar() {
  const { data: session } = useSession();

  const userInitials = getNameInitials(session?.user?.name);

  return <div className={classes.root}>{userInitials}</div>;
}
