/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LogoDiscord, LogoYoutube } from '@carbon/icons-react';
import clsx from 'clsx';

import { BLUESKY_LINK, DISCORD_LINK, YOUTUBE_LINK } from '@/constants';
import LogoBluesky from '@/svgs/LogoBluesky.svg';

import classes from './FooterNav.module.scss';

interface Props {
  className?: string;
}

export function FooterNav({ className }: Props) {
  return (
    <nav className={clsx(classes.root, className)}>
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
