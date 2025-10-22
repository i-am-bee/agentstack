/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { SkeletonIcon } from '@carbon/react';
import { useSession } from 'next-auth/react';

import { getNameInitials } from '#utils/helpers.ts';

import classes from './UserAvatar.module.scss';

export default function UserAvatar() {
  const { data: session, status } = useSession();

  const isLoading = status === 'loading';
  const userInitials = getNameInitials(session?.user?.name);

  if (isLoading) {
    return <UserAvatar.Skeleton />;
  }

  return <span className={classes.root}>{userInitials}</span>;
}

UserAvatar.Skeleton = function UserAvatarSkeleton() {
  return <SkeletonIcon className={classes.root} />;
};
