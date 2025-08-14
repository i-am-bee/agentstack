/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { LogoPython, Plug, Rocket, SettingsAdjust, Unlocked, WorkflowAutomation } from '@carbon/icons-react';
import { Theme, useTheme } from '@i-am-bee/beeai-ui';
import { useIsClient } from 'usehooks-ts';

import { FRAMEWORK_QUICKSTART_LINK } from '@/constants';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import FrameworkGraphicsDark from './assets/framework-diagram-dark.svg';
import FrameworkGraphicsLight from './assets/framework-diagram-light.svg';
import { FeaturesList } from './components/FeaturesList';
import { HeadlineWithLink } from './components/HeadlineWithLink';
import { TwoColumnGrid } from './components/TwoColumnGrid';
import classes from './Framework.module.scss';

export function Framework() {
  const { theme } = useTheme();
  const isClient = useIsClient();

  return (
    <section className={classes.root} id="framework">
      <LayoutContainer asGrid>
        <TwoColumnGrid className={classes.info}>
          <HeadlineWithLink
            title="Framework"
            description="Build production-ready AI agents with enterprise-grade reliability, built-in caching, memory optimization,
              resource management, and real-time monitoring."
            buttonProps={{ url: FRAMEWORK_QUICKSTART_LINK }}
            inverse
          />

          {isClient && (
            <div className={classes.graphics}>
              {theme === Theme.Light ? <FrameworkGraphicsLight /> : <FrameworkGraphicsDark />}
            </div>
          )}
        </TwoColumnGrid>

        <div className={classes.features}>
          <FeaturesList items={FEATURES_ITEMS} />
        </div>
      </LayoutContainer>
    </section>
  );
}

const FEATURES_ITEMS = [
  {
    icon: Rocket,
    content: (
      <>
        <strong>Production-ready from day one</strong> with built-in caching, memory optimization, resource management
        and real-time monitoring with OpenTelemetry integration.
      </>
    ),
  },
  {
    icon: WorkflowAutomation,
    content: (
      <>
        <strong>Workflow Orchestration</strong> connects agents seamlessly, passing tasks between them while maintaining
        context. Ensures reliable execution from simple to complex multi-agent processes.
      </>
    ),
  },
  {
    icon: LogoPython,
    content: (
      <>
        <strong>Python and TypeScript support</strong> with complete feature parity.
      </>
    ),
  },
  {
    icon: Unlocked,
    content: (
      <>
        <strong>No vendor lock-in</strong> - works with 10+ LLM providers, out-of-the-box.
      </>
    ),
  },
  {
    icon: SettingsAdjust,
    content: (
      <>
        <strong>Complete control over agent behavior</strong>, performance optimization, and resource allocation.
      </>
    ),
  },
  {
    icon: Plug,
    content: (
      <>
        <strong>Existing stack integration</strong> with MCP compatibility, custom tool development support, and
        seamless tool integration.
      </>
    ),
  },
];
