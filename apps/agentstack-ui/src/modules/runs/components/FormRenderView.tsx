/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormDemands } from 'agentstack-sdk';

import { Container } from '#components/layouts/Container.tsx';
import { FormRenderer } from '#modules/form/components/FormRenderer.tsx';
import type { RunFormValues } from '#modules/form/types.ts';

import { useAgentRun } from '../contexts/agent-run';
import classes from './FormRenderView.module.scss';

interface Props {
  formRender: FormDemands;
  onMessageSent?: () => void;
}

export function FormRenderView({ formRender, onMessageSent }: Props) {
  const { agent, submitForm } = useAgentRun();

  if (!formRender) {
    return false;
  }

  return (
    <Container size="sm" className={classes.root}>
      <FormRenderer
        definition={formRender}
        showRunSettings
        onSubmit={(values: RunFormValues) => {
          onMessageSent?.();
          const form = {
            request: formRender,
            response: { id: formRender.id, values },
          };
          submitForm(form);
        }}
        defaultHeading={agent.ui.user_greeting}
      />
    </Container>
  );
}
