/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { SkeletonIcon } from '@carbon/react';
import { useSession } from 'next-auth/react';

import classes from './UserAvatar.module.scss';

const getUserInitials = (name: string | null | undefined) => {
  if (!name) {
    return '';
  }

  // Names can have unicode characters in them, use unicode aware regex
  const matches = [...name.matchAll(/(\p{L}{1})\p{L}+/gu)];
  const initials = (matches.at(0)?.at(1) ?? '') + (matches.at(-1)?.at(1) ?? '');

  return initials.toUpperCase();
};

export default function UserAvatar() {
  const { data: session, status } = useSession();

  const isLoading = status === 'loading';
  const userInitials = getUserInitials(session?.user?.name);

  if (isLoading) {
    return <UserAvatar.Skeleton />;
  }

  return <span className={classes.root}>{userInitials}</span>;
}

UserAvatar.Skeleton = function UserAvatarSkeleton() {
  return <SkeletonIcon className={classes.root} />;
};
