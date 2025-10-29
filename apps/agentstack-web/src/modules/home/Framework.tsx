/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { Code, Constraint, FlowConnection, Plug, Shapes } from '@carbon/icons-react';
import { Theme, useTheme } from '@i-am-bee/agentstack-ui';
import { useIsClient } from 'usehooks-ts';

import { FRAMEWORK_INTRO_LINK } from '@/constants';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import FileConfigYaml from './assets/file-config-yaml.svg';
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
            title="BeeAI Framework"
            description="Build reliable, intelligent agents with our lightweight framework that goes beyond prompting and enforces rules."
            buttonProps={{ url: FRAMEWORK_INTRO_LINK }}
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
    icon: Constraint,
    title: 'Agents with constraints',
    content:
      "Preserve your agent's reasoning abilities while enforcing deterministic rules instead of suggesting behavior.",
  },
  {
    icon: FileConfigYaml,
    title: 'Declarative orchestration',
    content: 'Define complex agent systems in YAML for more predictable and maintainable orchestration.',
  },
  {
    icon: Plug,
    title: 'Pluggable observability',
    content:
      'Integrate with your existing stack in minutes with native OpenTelemetry support for auditing and monitoring.',
  },
  {
    icon: Code,
    title: 'Python and Typescript support',
    content: 'Feature parity between Python and TypeScript lets teams build with the tools they already know and love.',
  },
  {
    icon: Shapes,
    title: 'MCP and A2A native',
    content:
      'Build MCP-compatible components, equip agents with MCP tools, and interoperate with any MCP or A2A agent.',
  },
];
