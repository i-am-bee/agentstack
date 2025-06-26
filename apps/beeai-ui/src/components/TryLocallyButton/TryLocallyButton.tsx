/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowUpRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { TRY_LOCALLY_LINK } from '#utils/constants.ts';

import classes from './TryLocallyButton.module.scss';

export function TryLocallyButton() {
  return (
    <Button
      as="a"
      href={TRY_LOCALLY_LINK}
      target="_blank"
      rel="noreferrer"
      kind="primary"
      renderIcon={ArrowUpRight}
      size="md"
      className={classes.root}
    >
      Try locally in GUI
    </Button>
  );
}
