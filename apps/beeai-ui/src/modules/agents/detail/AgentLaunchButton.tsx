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
import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';
import isEmpty from 'lodash/isEmpty';
import type { ComponentProps } from 'react';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { SupportedUis } from '#modules/runs/constants.ts';
import { AddRequiredVariablesModal } from '#modules/variables/components/AddRequiredVariablesModal.tsx';
import { routes } from '#utils/router.ts';

import type { Agent, UiType } from '../api/types';
import { useMissingEnvs } from '../hooks/useMissingEnvs';
import { useProviderStatus } from '../hooks/useProviderStatus';
import classes from './AgentLaunchButton.module.scss';

interface Props {
  agent: Agent;
}

export function AgentLaunchButton({ agent }: Props) {
  const { openModal } = useModal();
  const { provider_id, annotations } = agent.metadata;
  const { missingEnvs, isPending: isMissingEnvsPending } = useMissingEnvs({ agent });
  const { isNotInstalled, isStarting, isError } = useProviderStatus({ providerId: provider_id });

  const uiType = annotations?.beeai_ui?.ui_type;
  const sharedProps: ComponentProps<typeof Button> = {
    kind: 'primary',
    size: 'md',
    className: classes.button,
  };

  if (isNotInstalled || isStarting || isError) {
    // TODO:
    return null;
  }

  if (uiType && SupportedUis.includes(uiType as UiType)) {
    return (
      // @ts-expect-error as prop mismatch to be resolved later, if component is used again
      <Button
        {...sharedProps}
        renderIcon={ArrowRight}
        disabled={isMissingEnvsPending}
        {...(isEmpty(missingEnvs)
          ? {
              as: TransitionLink,
              href: routes.agentRun({ name: agent.name }),
            }
          : {
              onClick: () => {
                openModal((props) => <AddRequiredVariablesModal {...props} missingEnvs={missingEnvs} />);
              },
            })}
      >
        Launch this agent
      </Button>
    );
  }

  return null;
}

AgentLaunchButton.Skeleton = function AgentLaunchButtonSkeleton() {
  /* .cds--layout--size-md fixes Carbon bug where button size prop is not respected */
  return <ButtonSkeleton size="md" className={clsx('cds--layout--size-md', classes.root)} />;
};
