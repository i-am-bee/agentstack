/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowUpRight } from '@carbon/icons-react';
import clsx from 'clsx';
import { usePathname } from 'next/navigation';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { groupNavItems } from '#modules/nav/groupNavItems.ts';
import { isActive } from '#modules/nav/isActive.ts';
import type { NavItem } from '#modules/nav/schema.ts';

import classes from './AppHeaderNav.module.scss';

interface Props {
  items: NavItem[];
}

export function AppHeaderNav({ items }: Props) {
  const pathname = usePathname();
  const groups = groupNavItems(items);

  return (
    <nav className={classes.nav}>
      {Object.entries(groups).map(([groupKey, group]) => (
        <ul key={groupKey} className={clsx(classes.ul, classes[groupKey])}>
          {group.map((item) => (
            <li key={item.label}>
              {item.isExternal ? (
                <ExternalLink {...item} />
              ) : (
                <InternalLink {...item} isActive={isActive(item, pathname ?? '')} />
              )}
            </li>
          ))}
        </ul>
      ))}
    </nav>
  );
}

const ExternalLink = ({ label, url, target = '_blank' }: NavItem) => (
  <a href={url} className={classes.link} target={target} rel="noreferrer">
    {label}
    <ArrowUpRight className={classes.icon} />
  </a>
);

const InternalLink = ({ label, url, isActive }: NavItem & { isActive?: boolean }) => (
  <TransitionLink href={url} className={clsx(classes.link, { [classes.active]: isActive })}>
    {label}
  </TransitionLink>
);
