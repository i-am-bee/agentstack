/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowLeft, Home } from '@carbon/icons-react';
import { usePathname } from 'next/navigation';
import { useMemo } from 'react';

import { routes } from '#utils/router.ts';

import { NavList } from './NavList';

export function MainNav() {
  const pathname = usePathname();

  const items = useMemo(() => {
    const homeHref = routes.home();
    const isHome = pathname === homeHref;

    return [
      {
        label: 'Home',
        href: homeHref,
        Icon: isHome ? Home : ArrowLeft,
        isActive: isHome,
      },
    ];
  }, [pathname]);

  return <NavList items={items} />;
}
