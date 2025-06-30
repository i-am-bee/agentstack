/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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
