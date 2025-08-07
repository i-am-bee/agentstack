/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { LogoPython, Rocket, SettingsAdjust, Unlocked } from '@carbon/icons-react';
import Image from 'next/image';

import { PLATFORM_QUICKSTART_LINK } from '@/constants';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import screenshotsImage from './assets/platform.png';
import { FeaturesList } from './components/FeaturesList';
import { HeadlineWithLink } from './components/HeadlineWithLink';
import classes from './Platform.module.scss';

export function Platform() {
  return (
    <div className={classes.root}>
      <LayoutContainer>
        <div className={classes.intro}>
          <HeadlineWithLink
            title="Platform"
            description="Deploy any AI agent with a custom web interface in minutes."
            buttonProps={{ url: PLATFORM_QUICKSTART_LINK }}
          />

          <div className={classes.introImage}>
            <Image src={screenshotsImage.src} width={1532} height={1126} alt="BeeAI UI & CLI" />
          </div>
        </div>

        <div className={classes.features}>
          <FeaturesList items={FEATURES_ITEMS} />
        </div>
      </LayoutContainer>
    </div>
  );
}

const FEATURES_ITEMS = [
  {
    icon: Rocket,
    content: (
      <>
        <strong>Create frontend interfaces</strong> for your Agents without a front end developer skillset
      </>
    ),
  },
  {
    icon: LogoPython,
    content: (
      <>
        <strong>Deploy agents from any framework</strong> — BeeAI, Langchain, CrewAI, or custom implementations
      </>
    ),
  },
  {
    icon: Unlocked,
    content: (
      <>
        Test agents with OpenAI, Anthropic, or <strong>10+ LLM providers</strong>
      </>
    ),
  },
  {
    icon: SettingsAdjust,
    content: (
      <>
        <strong>Enable agent interpretability</strong> by using A2A and the BeeAI SDK under the hood
      </>
    ),
  },
];
