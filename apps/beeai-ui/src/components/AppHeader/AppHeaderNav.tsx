/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { ArrowUpRight } from '@carbon/icons-react';
import clsx from 'clsx';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import type { NavItem } from '#modules/nav/schema.ts';

import classes from './AppHeaderNav.module.scss';

interface Props {
  items: NavItem[];
}

export function AppHeaderNav({ items }: Props) {
  const groups = {
    start: items.filter((item) => item.position !== 'end'),
    end: items.filter((item) => item.position === 'end'),
  };

  return (
    <nav className={classes.nav}>
      {Object.entries(groups).map(([groupKey, group]) => (
        <ul key={groupKey} className={classes.ul}>
          {group.map(({ label, url, isExternal, isActive }) => (
            <li key={label}>
              {isExternal ? (
                <ExternalLink label={label} url={url} />
              ) : (
                <InternalLink label={label} url={url} isActive={isActive} />
              )}
            </li>
          ))}
        </ul>
      ))}
    </nav>
  );
}

interface LinkProps {
  label: string;
  url: string;
  isActive?: boolean;
}

const ExternalLink = ({ label, url }: LinkProps) => (
  <a href={url} className={classes.link} target="_blank" rel="noreferrer">
    {label}
    <ArrowUpRight className={classes.icon} />
  </a>
);

const InternalLink = ({ label, url, isActive }: LinkProps) => (
  <TransitionLink href={url} className={clsx(classes.link, { [classes.active]: isActive })}>
    {label}
  </TransitionLink>
);
