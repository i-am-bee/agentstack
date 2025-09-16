/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname, useRouter } from 'next/navigation';

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
  const router = useRouter();
  const { start } = groupNavItems(items);
  const theItems: SideNavItem[] = start.map((item) => ({
    ...item,
    key: item.url,
    isActive: isActive(item, pathname ?? ''),
    onClick() {
      if (item.isExternal) {
        window.open(item.url, item.target ?? '_blank', 'noopener,noreferrer');
      } else {
        router.push(item.url);
      }
    },
  }));

  return (
    <NavGroup className={className} bodyClassName={bodyClassName}>
      <NavList items={theItems} />
    </NavGroup>
  );
}
