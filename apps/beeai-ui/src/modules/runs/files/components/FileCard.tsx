/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Close, Pdf, Warning } from '@carbon/icons-react';
import { IconButton, InlineLoading } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEventHandler } from 'react';

import { FileStatus } from '../types';
import { parseFilename } from '../utils';
import classes from './FileCard.module.scss';

interface Props {
  filename: string;
  href?: string;
  size?: 'sm' | 'md';
  status?: FileStatus;
  onRemoveClick?: MouseEventHandler;
}

export function FileCard({ filename, href, size = 'md', status, onRemoveClick }: Props) {
  const { name, ext } = parseFilename(filename);
  const isPending = status === FileStatus.Uploading;
  const isError = status === FileStatus.Failed;

  const Icon = {
    pdf: Pdf,
  }[ext];

  const content = (
    <>
      <span className={classes.name}>{name}</span>

      {ext && <span>.{ext}</span>}
    </>
  );

  return (
    <span
      className={clsx(classes.root, {
        [classes[size]]: size,
        [classes.isPending]: isPending,
        [classes.isError]: isError,
      })}
    >
      {isError && <Warning className={classes.errorIcon} />}

      {Icon && <Icon className={classes.icon} />}

      {href ? (
        <a href={href} target="_blank" rel="noreferrer" download={filename} className={classes.link}>
          {content}
        </a>
      ) : (
        content
      )}

      {isPending && <InlineLoading className={classes.loading} />}

      {onRemoveClick && !isPending && (
        <IconButton label="Remove" wrapperClasses={classes.remove} onClick={onRemoveClick}>
          <Close />
        </IconButton>
      )}
    </span>
  );
}
