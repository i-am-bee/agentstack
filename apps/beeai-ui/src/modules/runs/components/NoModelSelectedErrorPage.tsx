/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CopySnippet } from '#components/CopySnippet/CopySnippet.tsx';

import NoModelImage from './NoModelImage.svg';
import classes from './NoModelSelectedErrorPage.module.scss';

export function NoModelSelectedErrorPage() {
  return (
    <div className={classes.root}>
      <div className={classes.content}>
        <NoModelImage />
        <h1>
          Oooh, buzzkill.
          <br />
          There is no model selected.
        </h1>

        <div className={classes.description}>
          You can configure a model by running <CopySnippet className={classes.snippet}>beeai model setup</CopySnippet>{' '}
          in your terminal.
        </div>
      </div>
    </div>
  );
}
