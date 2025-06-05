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

import classes from './Source.module.scss';
import type { ResolvedSource, SourceReference } from './types';

interface Props {
  source: SourceReference;
  isActive?: boolean;
}

export function Source({ source, isActive }: Props) {
  // TODO:
  const {
    number,
    url,
    metadata: { title, description, faviconUrl },
  }: ResolvedSource = {
    ...source,
    metadata: {
      title: 'beeai-platform: Discover, run, and compose AI',
      description:
        'Orchestrate agents into workflows — regardless of how or where they were built . Key features. Feature, Description. ACP Native, Built from the ground.',
      faviconUrl: 'https://github.githubassets.com/favicons/favicon.svg',
    },
  };

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
          {faviconUrl && <img src={faviconUrl} className={classes.favicon} />}

          <span className={classes.url}>{url}</span>
        </p>
      </div>
    </article>
  );
}
