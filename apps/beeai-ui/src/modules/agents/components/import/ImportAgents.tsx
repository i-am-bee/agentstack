/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Add } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { useModal } from '#contexts/Modal/index.tsx';

import { ImportAgentsModal } from './ImportAgentsModal';

export function ImportAgents() {
  const { openModal } = useModal();

  return (
    <Button
      kind="tertiary"
      size="md"
      renderIcon={Add}
      onClick={() => openModal((props) => <ImportAgentsModal {...props} />)}
    >
      Import agents
    </Button>
  );
}
