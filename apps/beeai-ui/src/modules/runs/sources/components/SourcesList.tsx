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
