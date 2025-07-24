/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Accordion, AccordionItem } from '@carbon/react';
import clsx from 'clsx';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { useAutoScroll } from '#hooks/useAutoScroll.ts';
import { RunLogItem } from '#modules/runs/components/RunLogItem.tsx';

import type { ComposeStep } from '../contexts/compose-context';
import classes from './StepResult.module.scss';

interface Props {
  step: ComposeStep;
}

export function StepResult({ step }: Props) {
  const { isPending, logs, stats, result } = step;

  const isFinished = Boolean(!isPending && result);

  if (!(isPending || stats || result)) return null;

  return (
    <div className={clsx(classes.root, { [classes.finished]: isFinished, [classes.pending]: isPending })}>
      <Accordion>
        {logs?.length ? (
          <AccordionItem title="Logs" open={!isFinished ? isPending : undefined} className={classes.logsGroup}>
            <Logs logs={logs} />
          </AccordionItem>
        ) : null}

        {isFinished && (
          <AccordionItem
            className={clsx(classes.resultGroup, { [classes.empty]: !result })}
            title={
              <div className={classes.result}>
                <div>{isFinished ? 'Output' : null}</div>
              </div>
            }
          >
            <MarkdownContent>{result}</MarkdownContent>
          </AccordionItem>
        )}
      </Accordion>
    </div>
  );
}

function Logs({ logs }: { logs: string[] }) {
  const { ref: autoScrollRef } = useAutoScroll([logs.length]);

  return (
    <div className={classes.logs}>
      {logs?.map((message, order) => <RunLogItem key={order}>{message}</RunLogItem>)}
      <div ref={autoScrollRef} />
    </div>
  );
}
