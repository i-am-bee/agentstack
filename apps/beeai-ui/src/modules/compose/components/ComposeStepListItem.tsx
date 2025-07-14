/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import clsx from 'clsx';
import type { KeyboardEvent } from 'react';
import { useFormContext } from 'react-hook-form';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';

import { useCompose } from '../contexts';
import type { SequentialFormValues } from '../contexts/compose-context';
import classes from './ComposeStepListItem.module.scss';
import { StepResult } from './StepResult';

interface Props {
  idx: number;
}
export function ComposeStepListItem({ idx }: Props) {
  const { register, watch } = useFormContext<SequentialFormValues>();
  const {
    status,
    onSubmit,
    stepsFields: { remove },
  } = useCompose();

  const handleKeyDown = (event: KeyboardEvent) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      onSubmit();
    }
  };

  const step = watch(`steps.${idx}`);
  const { agent, isPending, stats, instruction } = step;

  const isViewMode = status !== 'ready';
  const isFinished = Boolean(!isPending && stats?.endTime);

  return (
    <div className={clsx(classes.root, classes[`status-${isPending ? 'pending' : isFinished ? 'finished' : 'ready'}`])}>
      <div className={classes.left}>
        <div className={classes.bullet}>{isPending ? <Spinner /> : <span>{idx + 1}</span>}</div>
      </div>
      <div className={classes.content}>
        <div className={classes.name}>{agent.ui.display_name}</div>

        <div className={classes.actions}>
          {!isViewMode && (
            <OverflowMenu aria-label="Options" size="md">
              <OverflowMenuItem itemText="Remove" onClick={() => remove(idx)} />
            </OverflowMenu>
          )}
        </div>

        <div className={classes.input}>
          {isViewMode ? (
            <p>{instruction}</p>
          ) : (
            <TextAreaAutoHeight
              className={classes.textarea}
              rows={3}
              placeholder="Write the agent prompt here"
              disabled={isViewMode}
              {...register(`steps.${idx}.instruction`, {
                required: true,
              })}
              onKeyDown={handleKeyDown}
            />
          )}
        </div>

        <StepResult step={step} />
      </div>
    </div>
  );
}
