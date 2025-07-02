/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, SkeletonIcon } from '@carbon/react';
import clsx from 'clsx';
import Image from 'next/image';
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
    title,
    metadata: { faviconUrl },
  } = data;

  return isPending ? (
    <Source.Skeleton />
  ) : faviconUrl ? (
    <span className={classes.source}>
      <Image src={faviconUrl} className={classes.icon} alt={title ?? ''} />
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
