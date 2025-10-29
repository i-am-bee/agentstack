/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link, Share } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { useCopyToClipboard } from 'usehooks-ts';

import { useToast } from '#contexts/Toast/index.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

interface Props {
  agent: Agent;
}

export function AgentShareButton({ agent }: Props) {
  const [, copy] = useCopyToClipboard();
  const { addToast } = useToast();

  const handleShare = () => {
    copy(`${window.location.origin}${routes.agentRun({ providerId: agent.provider.id })}`);
    addToast({ kind: 'info', subtitle: 'Link has been copied to clipboard!', icon: Link });
  };

  return (
    <Button kind="tertiary" size="sm" renderIcon={Share} onClick={handleShare}>
      Share agent
    </Button>
  );
}
