/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { FlowConnection, InsertPage, LogoPython, Plug, SettingsAdjust, Shapes } from '@carbon/icons-react';
import { Theme, useTheme } from '@i-am-bee/beeai-ui';
import { useIsClient } from 'usehooks-ts';

import { FRAMEWORK_QUICKSTART_LINK } from '@/constants';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import FrameworkGraphicsDark from './assets/framework-diagram-dark.svg';
import FrameworkGraphicsLight from './assets/framework-diagram-light.svg';
import type { FeatureItem } from './components/FeaturesList';
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
            title="beeai-framework"
            description="Build reliable, intelligent agents with our lightweight framework that goes beyond prompting and enforces rules."
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

const FEATURES_ITEMS: FeatureItem[] = [
  {
    icon: FlowConnection,
    title: 'Dynamic workflows',
    content:
      'Use simple decorators to design multi-agent systems with advanced patterns like parallelism, retries, and replanning.',
  },
  {
    icon: SettingsAdjust,
    title: 'Configuration over code',
    content: 'Define complex agent systems in YAML, for more predictable and maintainable orchestration.',
  },
  {
    icon: InsertPage,
    title: 'Modular by design',
    content:
      'Composable modules with stable interfaces give you a testable and maintainable foundation for production-grade AI.',
  },
  {
    icon: Plug,
    title: 'Pluggable observability',
    content:
      'Integrate with your existing stack in minutes with native OpenTelemetry support for auditing and monitoring.',
  },
  {
    icon: LogoPython,
    title: 'Dual-language support',
    content:
      'Feature parity between the Python and TypeScript lets teams build with the tools they already know and love.',
  },
  {
    icon: Shapes,
    title: 'Protocol native',
    content:
      'Build MCP-compatible components, equip agents with MCP tools, and interoperate with any MCP or A2A agent.',
  },
];
