/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Tools } from '@carbon/icons-react';

import { ApiKeyTag } from './ApiKeyTag';
import classes from './ToolCard.module.scss';

interface Props {
  onAddClick?: () => void;
}

export function ToolCard({ onAddClick }: Props) {
  return (
    <article className={classes.root}>
      <span className={classes.icon}>
        <Tools size={32} />
      </span>

      <h3 className={classes.heading}>Outlook</h3>

      <p className={classes.description}>
        Advanced reasoning and analysis to provide thoughtful, well-structured responses to complex questions and
        topics, lorem ipsum dolor sit amet...
      </p>

      <div className={classes.tag}>
        <ApiKeyTag onClick={onAddClick} />
      </div>
    </article>
  );
}
