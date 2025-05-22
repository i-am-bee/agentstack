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

import { LogoDiscord, LogoYoutube } from '@carbon/icons-react';
import clsx from 'clsx';

import LogoBluesky from '#svgs/LogoBluesky.svg';
import {
  ACP_DOCUMENTATION_LINK,
  BLUESKY_LINK,
  DISCORD_LINK,
  FRAMEWORK_GITHUB_REPO_LINK,
  YOUTUBE_LINK,
} from '#utils/constants.ts';

import classes from './FooterNav.module.scss';

interface Props {
  className?: string;
}

export function FooterNav({ className }: Props) {
  return (
    <nav className={clsx(classes.root, className)}>
      <ul className={classes.nav}>
        {NAV_ITEMS.map(({ label, href }) => (
          <li key={label} className={classes.item}>
            <a href={href} target="_blank" rel="noreferrer" aria-label={label} className={classes.link}>
              {label}
            </a>
          </li>
        ))}
      </ul>
      <hr />
      <ul className={clsx(classes.nav, classes.navSocial)}>
        {SOCIAL_NAV_ITEMS.map(({ label, href, Icon }) => (
          <li key={label} className={classes.item}>
            <a href={href} target="_blank" rel="noreferrer" aria-label={label} className={classes.link}>
              <Icon />
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
const NAV_ITEMS = [
  {
    label: 'BeeAI Framework',
    href: FRAMEWORK_GITHUB_REPO_LINK,
  },
  {
    label: 'ACP',
    href: ACP_DOCUMENTATION_LINK,
  },
];

const SOCIAL_NAV_ITEMS = [
  {
    label: 'Discord',
    href: DISCORD_LINK,
    Icon: LogoDiscord,
  },
  {
    label: 'YouTube',
    href: YOUTUBE_LINK,
    Icon: LogoYoutube,
  },
  {
    label: 'Bluesky',
    href: BLUESKY_LINK,
    Icon: LogoBluesky,
  },
];
