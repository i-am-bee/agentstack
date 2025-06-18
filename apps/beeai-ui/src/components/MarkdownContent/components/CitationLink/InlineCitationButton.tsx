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

import { Button, InlineLoading } from '@carbon/react';
import clsx from 'clsx';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import { useSource } from '#modules/runs/sources/api/queries/useSource.ts';
import type { SourceReference } from '#modules/runs/sources/api/types.ts';
import { resolveSource } from '#modules/runs/sources/utils.ts';

import classes from './InlineCitationButton.module.scss';
import { InlineCitationTooltipContent } from './InlineCitationTooltipContent';

interface Props {
  source: SourceReference;
  isActive?: boolean;
  onClick?: () => void;
}

export function InlineCitationButton({ source, isActive, onClick }: Props) {
  const { data, isPending } = useSource({ source });
  const resolvedSource = resolveSource({ source, data });

  return (
    <Tooltip
      size="lg"
      asChild
      content={
        isPending ? (
          <InlineLoading description="Loading&hellip;" className={classes.loading} />
        ) : (
          <InlineCitationTooltipContent source={resolvedSource} />
        )
      }
    >
      <Button className={clsx(classes.root, { [classes.isActive]: isActive })} onClick={onClick}>
        {source.number}
      </Button>
    </Tooltip>
  );
}
