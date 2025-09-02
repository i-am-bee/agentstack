/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSession } from 'next-auth/react';

export default function UserAvatar() {
  const { data: session } = useSession();
  let userInitials = '';
  if (session?.user?.name) {
    const namesArray = session.user.name.split(' ');
    const lastIndex = namesArray.length - 1;
    userInitials = namesArray[0][0] + ' ' + namesArray[lastIndex][0];
  }
  return (
    <div>
      <span>{userInitials}</span>
    </div>
  );
}
