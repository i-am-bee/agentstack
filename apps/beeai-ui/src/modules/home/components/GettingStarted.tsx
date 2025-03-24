/**
 * Copyright 2025 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use client';

import { CopySnippet } from '#components/CopySnippet/CopySnippet.tsx';
import { Container } from '#components/layouts/Container.tsx';
import { BREW_INSTALL_BEEAI } from '@i-am-bee/beeai-ui';
import classes from './GettingStarted.module.scss';
import { GitHubButton } from './GitHubButton';
import { LogoBeeAI } from './LogoBeeAI';
import { type VideoBeeAIProps, VideoBeeAI } from './VideoBeeAI';

interface GettingStartedProps {
  video: VideoBeeAIProps;
}

export function GettingStarted({ video }: GettingStartedProps) {
  return (
    <div className={classes.root}>
      <Container size="xs">
        <LogoBeeAI />

        <p className={classes.description}>
          The open-source platform to discover, run, and&nbsp;compose AI&nbsp;agents from&nbsp;any&nbsp;framework
        </p>

        <div className={classes.bottom}>
          <CopySnippet>{BREW_INSTALL_BEEAI}</CopySnippet>
          <GitHubButton />
        </div>
      </Container>

      <Container size="lg">
        <VideoBeeAI {...video} />
      </Container>
    </div>
  );
}
