/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { ArrowUpRight } from '@carbon/icons-react';
import { DOCUMENTATION_LINK, MainNav } from '@i-am-bee/beeai-ui';
import { usePathname } from 'next/navigation';

export function Navigation() {
  const pathname = usePathname();

  return (
    <MainNav
      items={items.map(({ section, ...item }) => ({ ...item, isActive: section && pathname?.startsWith(item.href) }))}
    />
  );
}

const items = [
  {
    label: <strong>BeeAI</strong>,
    href: '/',
  },
  {
    label: 'Agents',
    href: '/agents',
    section: true,
  },
  {
    label: 'Docs',
    href: DOCUMENTATION_LINK,
    Icon: ArrowUpRight,
    isExternal: true,
  },
];
