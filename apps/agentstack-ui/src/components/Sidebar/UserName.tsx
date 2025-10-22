/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonText } from '@carbon/react';
import { useSession } from 'next-auth/react';

import classes from './UserName.module.scss';

export function UserName() {
  const { data: session, status } = useSession();

  const isLoading = status === 'loading';
  const name = session?.user?.name;

  if (isLoading) {
    return <UserName.Skeleton />;
  }

  return <span className={classes.root}>{name}</span>;
}

UserName.Skeleton = function UserNameSkeleton() {
  return <SkeletonText width="50%" />;
};
