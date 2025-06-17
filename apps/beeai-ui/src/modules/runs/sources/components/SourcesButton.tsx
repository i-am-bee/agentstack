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

import { Button, SkeletonIcon } from '@carbon/react';
import clsx from 'clsx';
import pluralize from 'pluralize';

import { useSource } from '../api/queries/useSource';
import type { SourceReference } from '../api/types';
import classes from './SourcesButton.module.scss';

interface Props {
  sources: SourceReference[];
  isActive?: boolean;
  onClick?: () => void;
}

export function SourcesButton({ sources, isActive, onClick }: Props) {
  const count = sources.length;

  return (
    <Button kind="tertiary" className={clsx(classes.root, { [classes.isActive]: isActive })} onClick={onClick}>
      <span className={classes.sources}>
        {sources.slice(0, 5).map((source) => (
          <Source key={source.number} source={source} />
        ))}
      </span>

      <span>{pluralize('Source', count, true)}</span>
    </Button>
  );
}

interface SourceProps {
  source: SourceReference;
}

function Source({ source }: SourceProps) {
  const { data, isPending } = useSource({ source });

  if (!data) {
    return null;
  }

  const {
    metadata: { faviconUrl },
  } = data;

  return isPending ? (
    <Source.Skeleton />
  ) : (
    <span className={classes.source}>
      <img src={faviconUrl} className={classes.icon} />
    </span>
  );
}

Source.Skeleton = function SourceSkeleton() {
  return (
    <span className={classes.source}>
      <SkeletonIcon className={classes.icon} />
    </span>
  );
};
