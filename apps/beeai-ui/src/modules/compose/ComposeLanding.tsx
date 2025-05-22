/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
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

import { ArrowRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';
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
            const { id, name, route, description, image: Image } = workflow;
            return (
              <li
                key={id}
                className={classes.workflow}
                aria-disabled={!route}
                aria-selected={id === selected.id}
                onClick={() => route && setSelected(workflow)}
              >
                <div className={classes.workflowText}>
                  <span className={classes.name}>{name}</span>
                  <p>{description}</p>
                </div>
                <Image />
              </li>
            );
          })}
        </ul>

        <div className={classes.actionBar}>
          <TransitionLink href={selected.route} asChild>
            <Button renderIcon={ArrowRight} href={selected.route} className={classes.startBtn}>
              Start composing
            </Button>
          </TransitionLink>
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
