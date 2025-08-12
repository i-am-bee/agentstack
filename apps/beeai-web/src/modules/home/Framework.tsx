/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { LogoPython, Plug, Rocket, SettingsAdjust, Unlocked, WorkflowAutomation } from '@carbon/icons-react';

import { FRAMEWORK_QUICKSTART_LINK } from '@/constants';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import FrameworkGraphics from './assets/framework.svg';
import { FeaturesList } from './components/FeaturesList';
import { HeadlineWithLink } from './components/HeadlineWithLink';
import classes from './Framework.module.scss';

export function Framework() {
  return (
    <section className={classes.root}>
      <LayoutContainer>
        <div className={classes.info}>
          <HeadlineWithLink
            title="Framework"
            description="Build production-ready AI agents with enterprise-grade reliability, built-in caching, memory optimization,
              resource management, and real-time monitoring."
            buttonProps={{ url: FRAMEWORK_QUICKSTART_LINK }}
            inverse
          />

          <div className={classes.graphics}>
            <FrameworkGraphics />
          </div>
        </div>

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
        and real-time monitoring with OpenTelemetry integration
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
        <strong>Python and TypeScript support</strong> with complete feature parity
      </>
    ),
  },
  {
    icon: Unlocked,
    content: (
      <>
        <strong>No vendor lock-in</strong> - works with 10+ LLM providers out of the box
      </>
    ),
  },
  {
    icon: SettingsAdjust,
    content: (
      <>
        Maintain complete{' '}
        <strong>control over agent behavior, performance optimization, and resource allocation</strong>
      </>
    ),
  },
  {
    icon: Plug,
    content: (
      <>
        <strong>Integrates into your existing stack</strong> with MCP (Model Context Protocol) compatibility, custom
        tool development support, and seamless tool integration
      </>
    ),
  },
];
