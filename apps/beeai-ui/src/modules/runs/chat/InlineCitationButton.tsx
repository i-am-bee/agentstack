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

import { Button } from '@carbon/react';
import clsx from 'clsx';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';

import classes from './InlineCitationButton.module.scss';
import { InlineCitationTooltipContent } from './InlineCitationTooltipContent';
import type { ResolvedSource, SourceReference } from './types';

interface Props {
  source: SourceReference;
  isActive?: boolean;
}

export function InlineCitationButton({ source, isActive }: Props) {
  // TODO:
  const resolvedSource: ResolvedSource = {
    ...source,
    metadata: {
      title: 'beeai-platform: Discover, run, and compose AI',
      description:
        'Orchestrate agents into workflows — regardless of how or where they were built . Key features. Feature, Description. ACP Native, Built from the ground.',
      faviconUrl: 'https://github.githubassets.com/favicons/favicon.svg',
    },
  };

  return (
    <Tooltip size="lg" asChild content={<InlineCitationTooltipContent source={resolvedSource} />}>
      <Button className={clsx(classes.root, { [classes.isActive]: isActive })}>{source.number}</Button>
    </Tooltip>
  );
}
