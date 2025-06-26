/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Accordion, AccordionItem } from '@carbon/react';
import {
  ACP_DOCUMENTATION_LINK,
  COMPOSE_LINK,
  Container,
  FRAMEWORK_GITHUB_REPO_LINK,
  RUN_LINK,
} from '@i-am-bee/beeai-ui';
import { useState } from 'react';

import { TransitionLink } from '@/components/TransitionLink/TransitionLink';

import composeImage from './compose.png';
import discoverImage from './discover.png';
import classes from './ExperienceShowcase.module.scss';
import runImage from './run.png';
import { ShowcaseVideo } from './ShowcaseVideo';

export function ExperienceShowcase() {
  const [openItem, setOpenItem] = useState(Items.Discover);

  const posterSrc = {
    [Items.Discover]: discoverImage,
    [Items.Run]: runImage,
    [Items.Compose]: composeImage,
  }[openItem].src;

  const videoSrc = {
    [Items.Discover]: '/discover.mp4',
    [Items.Run]: '/run.mp4',
    [Items.Compose]: '/compose.mp4',
  }[openItem];

  return (
    <div className={classes.root}>
      <Container size="xxl">
        <div className={classes.holder}>
          <div className={classes.left}>
            <Accordion className={classes.accordion}>
              <AccordionItem
                title="Discover"
                open={openItem === Items.Discover}
                onClick={() => setOpenItem(Items.Discover)}
              >
                <p>
                  Browse agents and bring your own from any AI framework, including{' '}
                  <a href={FRAMEWORK_GITHUB_REPO_LINK} target="_blank" rel="noreferrer">
                    BeeAI Framework
                  </a>
                </p>

                <p className={classes.more}>
                  <TransitionLink href="/agents">Learn more</TransitionLink>
                </p>

                <ShowcaseVideo key={videoSrc} src={videoSrc} poster={posterSrc} className={classes.video} />
              </AccordionItem>

              <AccordionItem title="Run" open={openItem === Items.Run} onClick={() => setOpenItem(Items.Run)}>
                <p>Try agents through the CLI or GUI, connecting them to your choice of model provider</p>

                <p className={classes.more}>
                  <a href={RUN_LINK} target="_blank" rel="noreferrer">
                    Learn more
                  </a>
                </p>

                <ShowcaseVideo key={videoSrc} src={videoSrc} poster={posterSrc} className={classes.video} />
              </AccordionItem>

              <AccordionItem
                title="Compose"
                open={openItem === Items.Compose}
                onClick={() => setOpenItem(Items.Compose)}
              >
                <p>
                  Create multi-agent systems by quickly composing workflows powered by{' '}
                  <a href={ACP_DOCUMENTATION_LINK} target="_blank" rel="noreferrer">
                    ACP
                  </a>
                </p>

                <p className={classes.more}>
                  <a href={COMPOSE_LINK} target="_blank" rel="noreferrer">
                    Learn more
                  </a>
                </p>

                <ShowcaseVideo key={videoSrc} src={videoSrc} poster={posterSrc} className={classes.video} />
              </AccordionItem>
            </Accordion>
          </div>

          <div className={classes.right}>
            <ShowcaseVideo key={videoSrc} src={videoSrc} poster={posterSrc} />
          </div>
        </div>
      </Container>
    </div>
  );
}

enum Items {
  Discover = 'Discover',
  Run = 'Run',
  Compose = 'Compose',
}
