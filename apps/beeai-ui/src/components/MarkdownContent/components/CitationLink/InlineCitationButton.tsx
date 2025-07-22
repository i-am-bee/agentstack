/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Button } from '@carbon/react';
import clsx from 'clsx';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import type { UISourcePart } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import classes from './InlineCitationButton.module.scss';
import { InlineCitationTooltipContent } from './InlineCitationTooltipContent';

interface Props {
  source: UISourcePart;
  isActive?: boolean;
  onClick?: () => void;
}

export function InlineCitationButton({ source, isActive, onClick }: Props) {
  const { number } = source;

  return isNotNull(number) ? (
    <Tooltip size="lg" asChild content={<InlineCitationTooltipContent source={source} />}>
      <Button className={clsx(classes.root, { [classes.isActive]: isActive })} onClick={onClick}>
        {number}
      </Button>
    </Tooltip>
  ) : null;
}
