/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSession } from 'next-auth/react';

import classes from './UserAvatar.module.scss';

const getUserInitials = (name: string) => {
  if (!name) return '';

  // Names can have unicode characters in them, use unicode aware regex
  const matches = [...name.matchAll(/(\p{L}{1})\p{L}+/gu)];
  const initials = (matches.shift()?.[1] ?? '') + (matches.pop()?.[1] ?? '');
  return initials.toUpperCase();
};

export default function UserAvatar() {
  const { data: session } = useSession();
  let userInitials = '';
  if (session?.user?.name) {
    userInitials = getUserInitials(session.user.name);
  }
  return <div className={classes.root}>{userInitials}</div>;
}
