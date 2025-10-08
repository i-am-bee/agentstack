/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';

import { NavGroup } from '#components/SidePanel/NavGroup.tsx';
import type { NavItem as SideNavItem } from '#components/SidePanel/NavItem.tsx';
import { NavList } from '#components/SidePanel/NavList.tsx';
import { groupNavItems } from '#modules/nav/groupNavItems.ts';
import { isActive } from '#modules/nav/isActive.ts';
import type { NavItem } from '#modules/nav/schema.ts';

interface Props {
  items: NavItem[];
  className?: string;
  bodyClassName?: string;
}

export function CustomNav({ items, className, bodyClassName }: Props) {
  const pathname = usePathname();
  const { start } = groupNavItems(items);
  const theItems: SideNavItem[] = start.map((item) => ({
    ...item,
    key: item.url,
    href: item.url,
    isActive: isActive(item, pathname ?? ''),
  }));

  return (
    <NavGroup className={className} bodyClassName={bodyClassName}>
      <NavList items={theItems} />
    </NavGroup>
  );
}
