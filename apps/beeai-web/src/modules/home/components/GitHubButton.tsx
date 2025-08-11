/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LogoGithub } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { GITHUB_REPO_LINK } from '@/constants';

import classes from './GitHubButton.module.scss';

export function GitHubButton() {
  return (
    <Button
      as="a"
      href={GITHUB_REPO_LINK}
      target="_blank"
      rel="noreferrer"
      size="lg"
      className={classes.root}
      renderIcon={LogoGithub}
    >
      Hack with us on GitHub
    </Button>
  );
}
