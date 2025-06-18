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

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import { useApp } from '#contexts/App/index.ts';
import type { SourceReference } from '#modules/runs/sources/api/types.ts';
import { useSources } from '#modules/runs/sources/contexts/index.ts';

import { InlineCitationButton } from './InlineCitationButton';
import classes from './InlineCitations.module.scss';

interface Props {
  sources: SourceReference[] | undefined;
}

export function InlineCitations({ sources = [], children }: PropsWithChildren<Props>) {
  const { sourcesPanelOpen, showSourcesPanel } = useApp();
  const { activeSourceKey, setActiveMessageKey, setActiveSourceKey } = useSources();

  return sources.length > 0 ? (
    <span className={classes.root}>
      <span className={classes.content}>{children}</span>

      <span className={classes.list}>
        {sources.map((source) => {
          const { key, messageKey } = source;
          const isActive = sourcesPanelOpen && activeSourceKey === key;

          return (
            <sup key={key} className={clsx(classes.item, { [classes.isActive]: isActive })}>
              <InlineCitationButton
                source={source}
                isActive={isActive}
                onClick={() => {
                  setActiveMessageKey?.(messageKey);
                  setActiveSourceKey?.(key);
                  showSourcesPanel?.();
                }}
              />
            </sup>
          );
        })}
      </span>
    </span>
  ) : (
    children
  );
}
