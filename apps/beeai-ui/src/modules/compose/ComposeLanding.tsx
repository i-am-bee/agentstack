/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import { useState } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { VersionTag } from '#components/VersionTag/VersionTag.tsx';
import { routes } from '#utils/router.ts';

import SequentialIllustration from './assets/sequential.svg';
import SupervisorIllustration from './assets/supervisor.svg';
import classes from './ComposeLanding.module.scss';

export function ComposeLanding() {
  const [selected, setSelected] = useState<Workflow>(WORKFLOWS.at(0)!);

  return (
    <MainContent>
      <Container size="sm">
        <div className={classes.heading}>
          <h1>
            Compose playground <VersionTag>alpha</VersionTag>
          </h1>
          <p>Select a pattern to compose and test a multi-agent workflow</p>
        </div>

        <ul className={classes.workflows}>
          {WORKFLOWS.map((workflow) => {
            const { id, name, route, description, image: WorkflowImage } = workflow;
            return (
              <li
                key={id}
                className={clsx(classes.workflow, {
                  [classes.disabled]: !route,
                })}
                role="option"
                aria-selected={id === selected.id}
                aria-disabled={!route}
                onClick={() => route && setSelected(workflow)}
              >
                <div className={classes.workflowText}>
                  <span className={classes.name}>{name}</span>
                  <p>{description}</p>
                </div>
                <WorkflowImage />
              </li>
            );
          })}
        </ul>

        <div className={classes.actionBar}>
          <Button as={TransitionLink} renderIcon={ArrowRight} href={selected.route} className={classes.startBtn}>
            Start composing
          </Button>
        </div>
      </Container>
    </MainContent>
  );
}

const WORKFLOWS = [
  {
    id: 'sequential',
    name: 'Sequential',
    route: routes.playgroundSequential(),
    description: 'Define your agents and the sequence that makes sense for your workflow',
    image: SequentialIllustration,
  },
  {
    id: 'supervisor',
    name: 'Supervisor (coming soon)',
    description: 'Choose a supervisor agent to structure and control tasks of other agents in your system',
    image: SupervisorIllustration,
  },
];
type Workflow = (typeof WORKFLOWS)[number];
