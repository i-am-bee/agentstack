/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Share } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import type { RefObject } from 'react';
import { useRef, useState } from 'react';
import { useCopyToClipboard, useOnClickOutside } from 'usehooks-ts';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

interface Props {
  agent: Agent;
}

export function AgentShareButton({ agent }: Props) {
  const [, copy] = useCopyToClipboard();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [showCopied, setShowCopied] = useState(false);

  useOnClickOutside(buttonRef as RefObject<HTMLButtonElement>, () => setShowCopied(false));

  const handleShare = () => {
    copy(`${window.location.origin}${routes.agentRun({ providerId: agent.provider.id })}`);
    setShowCopied(true);
  };

  return (
    <Tooltip content="Link has been copied to clipboard!" isOpen={showCopied} placement="bottom" size="sm" asChild>
      <Button kind="tertiary" size="sm" renderIcon={Share} onClick={handleShare} ref={buttonRef}>
        Share agent
      </Button>
    </Tooltip>
  );
}
