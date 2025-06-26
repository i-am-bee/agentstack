/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useApp } from '#contexts/App/index.ts';

import type { SourceReference } from '../api/types';
import { useSources } from '../contexts';
import { Source } from './Source';
import classes from './SourcesList.module.scss';

interface Props {
  sources: SourceReference[];
}

export function SourcesList({ sources }: Props) {
  const { sourcesPanelOpen } = useApp();
  const { activeSourceKey } = useSources();

  return sources.length > 0 ? (
    <ul className={classes.root}>
      {sources.map((source) => {
        const isActive = sourcesPanelOpen && source.key === activeSourceKey;

        return (
          <li key={source.number}>
            <Source source={source} isActive={isActive} />
          </li>
        );
      })}
    </ul>
  ) : null;
}
