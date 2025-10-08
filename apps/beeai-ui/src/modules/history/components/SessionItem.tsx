/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ButtonSkeleton, OverflowMenu, OverflowMenuItem } from '@carbon/react';
import clsx from 'clsx';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useDeleteContext } from '#modules/platform-context/api/mutations/useDeleteContext.ts';
import { routes } from '#utils/router.ts';

import classes from './SessionItem.module.scss';

export interface SessionItem {
  contextId: string;
  providerId: string;
  href: string;
  heading: string;
  agentName?: string;
  isActive?: boolean;
}

export function SessionItem({ contextId, providerId, href, heading, agentName, isActive }: SessionItem) {
  const router = useRouter();
  const [optionsOpen, setOptionsOpen] = useState(false);

  const { mutateAsync: deleteContext } = useDeleteContext({
    onMutate: () => {
      if (isActive) {
        // TODO: should somehow invalidate the path
        router.push(routes.agentRun({ providerId }));
      }
    },
  });

  return (
    <li
      className={clsx(classes.root, {
        [classes.isActive]: isActive,
        [classes.optionsOpen]: optionsOpen,
      })}
    >
      <Link href={href} className={classes.link}>
        <span className={classes.heading}>{heading}</span>

        {agentName && <span className={classes.agentName}>{agentName}</span>}
      </Link>

      <div className={classes.options}>
        <OverflowMenu
          aria-label="Options"
          size="sm"
          onOpen={() => setOptionsOpen(true)}
          onClose={() => setOptionsOpen(false)}
        >
          <OverflowMenuItem itemText="Delete" isDelete onClick={() => deleteContext({ context_id: contextId })} />
        </OverflowMenu>
      </div>
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
