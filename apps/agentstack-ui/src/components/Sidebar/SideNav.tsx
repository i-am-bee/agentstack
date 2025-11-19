/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Settings } from '@carbon/icons-react';
import { usePathname } from 'next/navigation';
import { useMemo } from 'react';

import { routes } from '#utils/router.ts';

import { NavList } from './NavList';

export function SideNav() {
  const pathname = usePathname();

  const items = useMemo(() => {
    const settingsHref = routes.settings();

    return [
      {
        label: 'Settings',
        href: settingsHref,
        Icon: Settings,
        isActive: pathname === settingsHref,
      },
    ];
  }, [pathname]);

  return <NavList items={items} />;
}
