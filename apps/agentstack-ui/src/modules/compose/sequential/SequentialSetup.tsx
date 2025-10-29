/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowLeft, PlayFilledAlt, StopOutlineFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import { useFormState } from 'react-hook-form';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { VersionTag } from '#components/VersionTag/VersionTag.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { NewSessionButton } from '#modules/runs/components/NewSessionButton.tsx';
import { routes } from '#utils/router.ts';

import { AddAgentButton } from '../components/AddAgentButton';
import { ComposeStepListItem } from '../components/ComposeStepListItem';
import { useCompose } from '../contexts';
import { ComposeStatus, type SequentialFormValues } from '../contexts/compose-context';
import classes from './SequentialSetup.module.scss';

export function SequentialSetup() {
  const {
    onCancel,
    onSubmit,
    onReset,
    result,
    status,
    stepsFields: { append, fields },
  } = useCompose();
  const { contextId } = usePlatformContext();
  const { isValid } = useFormState<SequentialFormValues>();

  const isReady = status === ComposeStatus.Ready;
  const isPending = status === ComposeStatus.InProgress;
  const isCompleted = status === ComposeStatus.Completed;

  return (
    <form
      className={clsx(classes.form, { [classes.isSplitView]: Boolean(result) })}
      onSubmit={(e) => {
        e.preventDefault();

        if (!isValid) return;

        onSubmit();
      }}
    >
      <div className={classes.content}>
        <div className={classes.header}>
          <h1>
            {result ? (
              'Sequential workflow'
            ) : (
              <>
                Compose playground <VersionTag>alpha</VersionTag>
              </>
            )}
          </h1>

          {isCompleted && <NewSessionButton onClick={() => onReset()} />}
        </div>

        <h2 className={classes.label}>Sequence</h2>
        <div className={classes.agents}>
          {fields.map((field, idx) => (
            <ComposeStepListItem key={field.id} idx={idx} />
          ))}

          {isReady && (
            <AddAgentButton
              isDisabled={isPending}
              onSelectAgent={(agent: Agent) => {
                append({ agent, instruction: '', status: ComposeStatus.Ready });
              }}
            />
          )}
        </div>
      </div>

      <div className={classes.actionBar}>
        <Button as={TransitionLink} kind="ghost" size="md" className={classes.backButton} href={routes.playground()}>
          <ArrowLeft /> Back to patterns
        </Button>

        {!isCompleted &&
          (!isPending ? (
            <Button
              type="submit"
              renderIcon={PlayFilledAlt}
              kind="primary"
              size="md"
              iconDescription="Send"
              disabled={isPending || !isValid || !fields.length || !contextId}
            >
              Run
            </Button>
          ) : (
            <Button
              renderIcon={StopOutlineFilled}
              kind="tertiary"
              size="md"
              iconDescription="Cancel"
              onClick={(e) => {
                onCancel();
                e.preventDefault();
              }}
            >
              Stop
            </Button>
          ))}
      </div>
    </form>
  );
}
