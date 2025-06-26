/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LogoGithub } from '@carbon/icons-react';

import { GITHUB_REPO_LINK } from '#utils/constants.ts';

import classes from './GitHubLink.module.scss';

export function GitHubLink() {
  return (
    <a href={GITHUB_REPO_LINK} target="_blank" rel="noreferrer" className={classes.root}>
      <span>GitHub</span>
      <LogoGithub />
    </a>
  );
}
