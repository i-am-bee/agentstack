/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import type { UISourcePart } from '#modules/messages/types.ts';

import { useSources } from '../contexts';
import { Source } from './Source';
import classes from './SourcesList.module.scss';

interface Props {
  sources: UISourcePart[];
}

export function SourcesList({ sources }: Props) {
  const { activeSidePanel } = useApp();
  const { activeSource } = useSources();

  const hasSources = sources.length > 0;

  if (!hasSources) {
    return null;
  }

  return (
    <ul className={classes.root}>
      {sources.map((source) => {
        const { id } = source;
        const isActive = activeSidePanel === SidePanelVariant.Sources && activeSource?.id === id;

        return (
          <li key={id}>
            <Source source={source} isActive={isActive} />
          </li>
        );
      })}
    </ul>
  );
}
