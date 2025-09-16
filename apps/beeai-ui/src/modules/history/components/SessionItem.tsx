/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';
import Link from 'next/link';

import classes from './SessionItem.module.scss';

export interface SessionItem {
  href: string;
  heading: string;
  agentName?: string;
  isActive?: boolean;
}

export function SessionItem({ href, heading, agentName, isActive }: SessionItem) {
  return (
    <li>
      <Link href={href} className={clsx(classes.link, { [classes.isActive]: isActive })}>
        <span className={classes.heading}>{heading}</span>

        {agentName && <span className={classes.agentName}>{agentName}</span>}
      </Link>
    </li>
  );
}

SessionItem.Skeleton = function NavItemSkeleton() {
  return (
    <li>
      <ButtonSkeleton className={classes.skeleton} />
    </li>
  );
};
