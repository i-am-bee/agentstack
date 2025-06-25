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

import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import clsx from 'clsx';
import type { KeyboardEvent } from 'react';
import { useFormContext } from 'react-hook-form';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';

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
  const { display_name } = getAgentUiMetadata(agent);

  const isViewMode = status !== 'ready';
  const isFinished = Boolean(!isPending && stats?.endTime);

  return (
    <div className={clsx(classes.root, classes[`status-${isPending ? 'pending' : isFinished ? 'finished' : 'ready'}`])}>
      <div className={classes.left}>
        <div className={classes.bullet}>{isPending ? <Spinner /> : <span>{idx + 1}</span>}</div>
      </div>
      <div className={classes.content}>
        <div className={classes.name}>{display_name}</div>

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
