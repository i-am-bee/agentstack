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

import { Close, Pdf, Warning } from '@carbon/icons-react';
import { IconButton, InlineLoading } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEventHandler } from 'react';

import { parseFilename } from '../utils';
import classes from './FileCard.module.scss';

interface Props {
  filename: string;
  href?: string;
  size?: 'sm' | 'md';
  isPending?: boolean;
  isError?: boolean;
  onRemoveClick?: MouseEventHandler;
}

export function FileCard({ filename, href, size = 'md', isPending, isError, onRemoveClick }: Props) {
  const { name, ext } = parseFilename(filename);

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
        <a href={href} download={filename} className={classes.link}>
          {content}
        </a>
      ) : (
        content
      )}

      {isPending && <InlineLoading className={classes.loading} />}

      {onRemoveClick && (
        <IconButton label="Remove" wrapperClasses={classes.remove} onClick={onRemoveClick}>
          <Close />
        </IconButton>
      )}
    </span>
  );
}
