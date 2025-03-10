/**
 * Copyright 2025 IBM Corp.
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

import { PlayFilledAlt } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import { useForm } from 'react-hook-form';
import { InputBar } from '../components/InputBar';
import { useHandsOff } from '../contexts/hands-off';
import classes from './HandsOffInput.module.scss';

export function HandsOffInput() {
  const { onSubmit, input, text, isPending } = useHandsOff();

  const form = useForm<FormValues>({
    mode: 'onChange',
    defaultValues: {},
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = form;

  const isSubmitDisabled = isSubmitting;
  const isPendingOrText = Boolean(isPending || text);
  const isFinal = Boolean(text && !isPending);

  return (
    <div className={clsx(classes.root, { [classes.isPendingOrText]: isPendingOrText })}>
      <h2 className={classes.heading}>{isFinal ? 'Task input:' : 'What is your research task?'}</h2>

      {isPendingOrText ? (
        <h2 className={classes.input}>{input?.text}</h2>
      ) : (
        <InputBar
          onSubmit={() => {
            handleSubmit(async ({ input }) => {
              await onSubmit(input);

              reset();
            })();
          }}
          isSubmitDisabled={isSubmitDisabled}
          inputProps={{
            placeholder: 'Write a research report about…',
            ...register('input', { required: true }),
          }}
        >
          <Button type="submit" renderIcon={PlayFilledAlt} size="sm" disabled={isSubmitDisabled}>
            Run
          </Button>
        </InputBar>
      )}
    </div>
  );
}

export interface FormValues {
  input: string;
}
