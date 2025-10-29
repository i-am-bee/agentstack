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

export function NoModelSelectedErrorPage() {
  return (
    <div className={classes.root}>
      <Container size="md" className={classes.container}>
        <div className={classes.content}>
          <NoModelImage />
          <h1>
            Oooh, buzzkill.
            <br />
            There is no model selected.
          </h1>

          <div className={classes.description}>
            You can configure a model by running{' '}
            <CopySnippet className={classes.snippet}>{MODEL_SETUP_COMMAND}</CopySnippet> in your terminal.
          </div>
        </div>
        <div className={classes.footer}>
          Need more information? Visit our <ExternalLink href={DOCUMENTATION_LINK}>documentation</ExternalLink>.
        </div>
      </Container>
    </div>
  );
}
