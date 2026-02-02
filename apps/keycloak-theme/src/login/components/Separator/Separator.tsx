/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import classes from './Separator.module.scss';

interface SeparatorProps {
  text?: string;
}

export function Separator({ text }: SeparatorProps) {
  return <div className={classes.root}>{text && <span className={classes.text}>{text}</span>}</div>;
}
