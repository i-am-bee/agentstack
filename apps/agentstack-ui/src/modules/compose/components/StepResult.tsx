/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Accordion, AccordionItem } from '@carbon/react';
import clsx from 'clsx';
import { useMemo } from 'react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { useAutoScroll } from '#hooks/useAutoScroll.ts';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { getMessageRawContent, getMessageTrajectories } from '#modules/messages/utils.ts';
import { TrajectoryList } from '#modules/trajectories/components/TrajectoryList.tsx';
import { hasViewableTrajectoryParts } from '#modules/trajectories/utils.ts';

import { ComposeStatus, type ComposeStep } from '../contexts/compose-context';
import classes from './StepResult.module.scss';

interface Props {
  step: ComposeStep;
}

export function StepResult({ step }: Props) {
  const { status, stats, result } = step;

  const isFinished = status === ComposeStatus.Completed;
  const isPending = status === ComposeStatus.InProgress;

  const rawContent = useMemo(() => result && getMessageRawContent(result), [result]);

  if (!(isPending || stats || result)) return null;

  const trajectories = result && getMessageTrajectories(result).filter(hasViewableTrajectoryParts);

  return (
    <div className={clsx(classes.root, { [classes.finished]: isFinished, [classes.pending]: isPending })}>
      <Accordion>
        {isFinished && (
          <AccordionItem
            className={clsx(classes.resultGroup, { [classes.empty]: !result })}
            title={
              <div className={classes.result}>
                <div>{isFinished ? 'Output' : null}</div>
              </div>
            }
          >
            <MarkdownContent>{rawContent}</MarkdownContent>
          </AccordionItem>
        )}
        {trajectories?.length ? (
          <AccordionItem title="How did I get this answer?" open={!isFinished ? isPending : undefined}>
            <Trajectories trajectories={trajectories} />
          </AccordionItem>
        ) : null}
      </Accordion>
    </div>
  );
}

function Trajectories({ trajectories }: { trajectories: UITrajectoryPart[] }) {
  const { ref: autoScrollRef } = useAutoScroll([trajectories.length]);

  return (
    <div className={classes.trajectories}>
      <TrajectoryList trajectories={trajectories} isOpen />
      <div ref={autoScrollRef} />
    </div>
  );
}
