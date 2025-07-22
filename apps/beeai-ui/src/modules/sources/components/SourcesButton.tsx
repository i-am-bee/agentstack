/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, SkeletonIcon } from '@carbon/react';
import clsx from 'clsx';
import pluralize from 'pluralize';

import type { UISourcePart } from '#modules/messages/types.ts';

import classes from './SourcesButton.module.scss';

interface Props {
  sources: UISourcePart[];
  isActive?: boolean;
  onClick?: () => void;
}

export function SourcesButton({ sources, isActive, onClick }: Props) {
  const count = sources.length;

  return (
    <Button kind="tertiary" className={clsx(classes.root, { [classes.isActive]: isActive })} onClick={onClick}>
      <span className={classes.sources}>
        {sources.slice(0, 5).map((source) => (
          <Source key={source.id} source={source} />
        ))}
      </span>

      <span>{pluralize('Source', count, true)}</span>
    </Button>
  );
}

interface SourceProps {
  source: UISourcePart;
}

function Source({ source }: SourceProps) {
  const { title, faviconUrl } = source;

  return faviconUrl ? (
    <span className={classes.source}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={faviconUrl} className={classes.icon} alt={title ?? ''} />
    </span>
  ) : null;
}

Source.Skeleton = function SourceSkeleton() {
  return (
    <span className={classes.source}>
      <SkeletonIcon className={classes.icon} />
    </span>
  );
};
