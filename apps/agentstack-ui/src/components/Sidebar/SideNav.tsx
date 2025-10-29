/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Document } from '@carbon/icons-react';
import { useMemo } from 'react';

import { DOCUMENTATION_LINK } from '#utils/constants.ts';

import { NavList } from './NavList';

export function SideNav() {
  const items = useMemo(
    () => [
      {
        label: 'Documentation',
        href: DOCUMENTATION_LINK,
        Icon: Document,
        isExternal: true,
      },
    ],
    [],
  );

  return <NavList items={items} />;
}
