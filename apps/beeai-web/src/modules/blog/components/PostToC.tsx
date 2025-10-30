/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useScrollableContainer } from '@i-am-bee/agentstack-ui';
import clsx from 'clsx';
import { useMemo, useRef } from 'react';

import { useSections } from '@/hooks/useSections';

import type { PostToCItem } from '../types';
import classes from './PostToC.module.scss';

interface Props {
  items: PostToCItem[];
}

export function PostToC({ items }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const scrollableContainer = useScrollableContainer(ref.current);

  const filteredItems = useMemo(() => items.filter(({ depth }) => depth === 2), [items]);
  const hasItems = filteredItems.length > 0;

  const { activeHref, handleClick } = useSections({ scrollableContainer, items: filteredItems });

  if (!hasItems) {
    return null;
  }

  return (
    <div className={classes.root} ref={ref}>
      <h3 className={classes.heading}>Table of content</h3>

      <ul>
        {filteredItems.map(({ href, value }) => {
          const isActive = activeHref === href;

          return (
            <li key={href}>
              <a
                href={href}
                className={clsx(classes.link, { [classes.isActive]: isActive })}
                onClick={(event) => handleClick(event, href)}
              >
                <span className={classes.label}>{value}</span>
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
