/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { FRAMEWORK_QUICKSTART_LINK } from '@/constants';

import classes from './PrimaryCTALink.module.scss';

export function PrimaryCTALink() {
  return (
    <Button
      as="a"
      href={FRAMEWORK_QUICKSTART_LINK}
      target="_blank"
      rel="noreferrer"
      size="lg"
      className={classes.root}
      renderIcon={ArrowRight}
    >
      Get started
    </Button>
  );
}
