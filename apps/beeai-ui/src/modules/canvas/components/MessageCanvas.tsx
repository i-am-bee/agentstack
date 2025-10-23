/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIAgentMessage } from '#modules/messages/types.ts';

import { CanvasCard } from './CanvasCard';
import classes from './CanvasCard.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function MessageCanvas({ message }: Props) {
  console.log(message);

  return (
    <CanvasCard
      className={classes.root}
      heading="Cozy Winter Dinner Party Menu"
      onClick={() => console.log('open canvas')}
    />
  );
}
