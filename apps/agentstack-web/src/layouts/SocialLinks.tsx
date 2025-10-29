/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LogoDiscord, LogoGithub } from '@carbon/icons-react';

import { DISCORD_LINK, GITHUB_LINK } from '@/constants';

import classes from './SocialLinks.module.scss';

export function SocialLinks() {
  return (
    <ul className={classes.socialLinks}>
      {ITEMS.map(({ href, label, Icon }) => (
        <li key={href}>
          <a href={href} target="_blank" rel="noreferrer">
            <span>{label}</span>
            <Icon />
          </a>
        </li>
      ))}
    </ul>
  );
}

const ITEMS = [
  { href: DISCORD_LINK, label: 'Discord', Icon: LogoDiscord },
  { href: GITHUB_LINK, label: 'GitHub', Icon: LogoGithub },
];
