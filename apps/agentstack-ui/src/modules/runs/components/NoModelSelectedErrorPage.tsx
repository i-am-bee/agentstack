/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CopySnippet } from '#components/CopySnippet/CopySnippet.tsx';
import { Container } from '#components/layouts/Container.tsx';
import { ExternalLink } from '#components/MarkdownContent/components/ExternalLink.tsx';
import { DOCUMENTATION_LINK, MODEL_SETUP_COMMAND } from '#utils/constants.ts';

import NoModelImage from './NoModelImage.svg';
import classes from './NoModelSelectedErrorPage.module.scss';

interface Props {
  type?: ModelType;
}

export function NoModelSelectedErrorPage({ type = ModelType.Llm }: Props) {
  const { label, labelWithArticle, command } = MODEL_TYPE_INFO[type];

  return (
    <div className={classes.root}>
      <Container size="md" className={classes.container}>
        <div className={classes.content}>
          <NoModelImage />
          <h1>
            Oooh, buzzkill.
            <br />
            There is no {label} selected.
          </h1>

          <div className={classes.description}>
            You can configure {labelWithArticle} by running{' '}
            <CopySnippet className={classes.snippet}>{command}</CopySnippet> in your terminal.
          </div>
        </div>
        <div className={classes.footer}>
          Need more information? Visit our <ExternalLink href={DOCUMENTATION_LINK}>documentation</ExternalLink>.
        </div>
      </Container>
    </div>
  );
}

export enum ModelType {
  Llm = 'Llm',
  Embedding = 'Embedding',
}

const MODEL_TYPE_INFO = {
  [ModelType.Llm]: {
    label: 'model',
    labelWithArticle: 'a model',
    command: MODEL_SETUP_COMMAND,
  },
  [ModelType.Embedding]: {
    label: 'embedding model',
    labelWithArticle: 'an embedding model',
    command: 'agentstack model add embedding',
  },
};
