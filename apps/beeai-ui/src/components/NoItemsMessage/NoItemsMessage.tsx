/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import classes from './NoItemsMessage.module.scss';

interface Props {
  message: string;
}

export function NoItemsMessage({ message }: Props) {
  return <p className={classes.empty}>{message}</p>;
}
