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

import { ArrowUpRight, Asleep, Awake, LogoDiscord, LogoGithub, LogoYoutube, Settings } from '@carbon/icons-react';
import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import { useMemo } from 'react';

import { useTheme } from '#contexts/Theme/index.ts';
import { Theme } from '#contexts/Theme/types.ts';
import { useViewTransition } from '#hooks/useViewTransition.ts';
import LogoBluesky from '#svgs/LogoBluesky.svg';
import { BLUESKY_LINK, DISCORD_LINK, DOCUMENTATION_LINK, GITHUB_REPO_LINK, YOUTUBE_LINK } from '#utils/constants.ts';
import { routes } from '#utils/router.ts';

import classes from './UserNav.module.scss';

export function UserNav() {
  const { transitionTo } = useViewTransition();
  const { theme, toggleTheme } = useTheme();

  const items = useMemo(
    () => [
      {
        itemText: 'App settings',
        href: routes.settings(),
        isInternal: true,
      },
      {
        itemText: 'Toggle theme',
        icon: theme === Theme.Light ? Awake : Asleep,
        onClick: toggleTheme,
      },
      {
        groupLabel: 'Get support',
      },
      {
        itemText: 'Documentation',
        href: DOCUMENTATION_LINK,
        icon: ArrowUpRight,
      },
      {
        itemText: 'Discord',
        href: DISCORD_LINK,
        icon: LogoDiscord,
      },
      {
        groupLabel: 'Learn more',
      },
      {
        itemText: 'GitHub',
        href: GITHUB_REPO_LINK,
        icon: LogoGithub,
      },
      {
        itemText: 'YouTube',
        href: YOUTUBE_LINK,
        icon: LogoYoutube,
      },
      {
        itemText: 'Bluesky',
        href: BLUESKY_LINK,
        icon: LogoBluesky,
      },
    ],
    [theme, toggleTheme],
  );

  return (
    <OverflowMenu
      renderIcon={Settings}
      size="sm"
      aria-label="User navigation"
      direction="top"
      className={classes.button}
    >
      {items.map(({ groupLabel, itemText, icon: Icon, isInternal, href, onClick, ...props }, idx) => {
        return groupLabel ? (
          <OverflowMenuItem
            key={idx}
            itemText={<span className="cds--overflow-menu-options__option-content">{groupLabel}</span>}
            wrapperClassName="cds--overflow-menu-options__option--group-label"
            disabled
            hasDivider
          />
        ) : (
          <OverflowMenuItem
            key={idx}
            {...props}
            href={href}
            target={!isInternal ? '_blank' : undefined}
            onClick={(event) => {
              if (isInternal) {
                transitionTo(href);
                event.preventDefault();
              }

              onClick?.();
            }}
            itemText={
              Icon ? (
                <>
                  <span className="cds--overflow-menu-options__option-content">{itemText}</span> <Icon />
                </>
              ) : (
                itemText
              )
            }
          />
        );
      })}
    </OverflowMenu>
  );
}
