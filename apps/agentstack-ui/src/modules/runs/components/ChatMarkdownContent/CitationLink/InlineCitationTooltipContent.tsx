/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowUpRight } from '@carbon/icons-react';

import type { UISourcePart } from '#modules/messages/types.ts';

import classes from './InlineCitationTooltipContent.module.scss';

interface Props {
  source: UISourcePart;
}

export function InlineCitationTooltipContent({ source }: Props) {
  const { url, title, description, faviconUrl } = source;

  return (
    <div className={classes.root}>
      <h2 className={classes.heading}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {faviconUrl && <img src={faviconUrl} className={classes.favicon} alt={title} />}

        <a href={url} target="_blank" rel="noreferrer" className={classes.title}>
          {title ?? url}
        </a>

        <ArrowUpRight className={classes.icon} />
      </h2>

      {description && <p className={classes.description}>{description}</p>}

      <p className={classes.url}>{url}</p>
    </div>
  );
}
