/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { Deploy, Gui, Unlocked } from '@carbon/icons-react';
import Image from 'next/image';

import { PLATFORM_INTRO_LINK } from '@/constants';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import InterfaceUsageAlt from './assets/interface-usage-alt.svg';
import screenshotsImage from './assets/platform.png';
import type { FeatureItem } from './components/FeaturesList';
import { FeaturesList } from './components/FeaturesList';
import { HeadlineWithLink } from './components/HeadlineWithLink';
import { TwoColumnGrid } from './components/TwoColumnGrid';
import classes from './Platform.module.scss';

export function Platform() {
  return (
    <section className={classes.root} id="platform">
      <LayoutContainer>
        <TwoColumnGrid className={classes.info}>
          <div className={classes.infoLeft}>
            <HeadlineWithLink
              title="beeai-platform"
              description="Test, debug, and share your agents in an interactive UI with out-of-the-box trajectory, citations, and more."
              buttonProps={{ url: PLATFORM_INTRO_LINK }}
            />
          </div>

          <div className={classes.graphics}>
            <Image src={screenshotsImage} width={1532} height={1126} alt="BeeAI UI & CLI" />
          </div>
        </TwoColumnGrid>

        <div className={classes.features}>
          <FeaturesList items={FEATURES_ITEMS} />
        </div>
      </LayoutContainer>
    </section>
  );
}

const FEATURES_ITEMS: FeatureItem[] = [
  {
    icon: Gui,
    title: 'Instant agent UI',
    content:
      "Generate a shareable front-end from your code in minutes. Focus on your agent's logic, not UI frameworks.",
  },
  {
    icon: InterfaceUsageAlt,
    title: 'Effortless deployment',
    content:
      'Go from container to production-ready. We handle database, storage, scaling, and RAG so you can focus on your agent.',
  },
  {
    icon: Unlocked,
    title: 'Multi-provider playground',
    content:
      'Test across OpenAI, Anthropic, Gemini, IBM watsonx, Ollama and more. Instantly compare performance and cost to find the optimal model.',
  },
  {
    icon: Deploy,
    title: 'Framework-agnostic',
    content:
      'Run agents from LangChain, CrewAI, BeeAI and more on a single platform. Enable cross-framework collaboration without rewriting your code.',
  },
];
