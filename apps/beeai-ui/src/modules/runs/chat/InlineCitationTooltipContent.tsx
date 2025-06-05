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

import { ArrowUpRight } from '@carbon/icons-react';

import classes from './InlineCitationTooltipContent.module.scss';
import type { ResolvedSource } from './types';

interface Props {
  source: ResolvedSource;
}

export function InlineCitationTooltipContent({ source }: Props) {
  const {
    url,
    metadata: { title, description, faviconUrl },
  } = source;

  return (
    <div className={classes.root}>
      <h2 className={classes.heading}>
        {faviconUrl && <img src={faviconUrl} className={classes.favicon} />}

        <a href={url} target="_blank" rel="noreferrer" className={classes.title}>
          {title}
        </a>

        <ArrowUpRight className={classes.icon} />
      </h2>

      {description && <p className={classes.description}>{description}</p>}

      <p className={classes.url}>{url}</p>
    </div>
  );
}
