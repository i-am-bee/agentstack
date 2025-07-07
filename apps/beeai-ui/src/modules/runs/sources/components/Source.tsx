/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonPlaceholder, SkeletonText } from '@carbon/react';
import clsx from 'clsx';

import { useSource } from '../api/queries/useSource';
import type { SourceReference } from '../api/types';
import { resolveSource } from '../utils';
import classes from './Source.module.scss';

interface Props {
  source: SourceReference;
  isActive?: boolean;
}

export function Source({ source, isActive }: Props) {
  const { data, isPending } = useSource({ source });
  const resolvedSource = resolveSource({ source, data });

  if (isPending) {
    return <Source.Skeleton />;
  }

  const {
    number,
    url,
    metadata: { title, description, faviconUrl },
  } = resolvedSource;

  return (
    <article className={clsx(classes.root, { [classes.isActive]: isActive })}>
      <p className={classes.number}>{number}</p>

      <div className={classes.body}>
        <h3 className={classes.heading}>
          <a href={url} target="_blank" rel="noreferrer" className={classes.link}>
            {title}
          </a>
        </h3>

        {description && <p className={classes.description}>{description}</p>}

        <p className={classes.footer}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {faviconUrl && <img src={faviconUrl} className={classes.favicon} alt={title} />}

          <span className={classes.url}>{url}</span>
        </p>
      </div>
    </article>
  );
}

Source.Skeleton = function SourceSkeleton() {
  return (
    <article className={classes.root}>
      <SkeletonPlaceholder className={classes.number} />

      <div className={classes.body}>
        <SkeletonText className={classes.heading} />

        <SkeletonText paragraph lineCount={2} className={classes.description} />

        <div className={classes.footer}>
          <SkeletonText className={classes.url} />
        </div>
      </div>
    </article>
  );
};
