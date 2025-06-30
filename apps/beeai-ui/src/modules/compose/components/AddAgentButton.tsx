/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Add } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import type { RefObject } from 'react';
import { useId, useRef, useState } from 'react';
import { useOnClickOutside } from 'usehooks-ts';

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';
import type { Agent } from '#modules/agents/api/types.ts';

import { useSequentialCompatibleAgents } from '../hooks/useSequentialCompatibleAgents';
import classes from './AddAgentButton.module.scss';
import { AgentListOption } from './AgentListOption';

interface Props {
  onSelectAgent: (agent: Agent) => void;
  isDisabled?: boolean;
}

export function AddAgentButton({ onSelectAgent, isDisabled }: Props) {
  const id = useId();
  const [expanded, setExpanded] = useState(false);

  const selectorRef = useRef<HTMLDivElement>(null);

  useOnClickOutside(selectorRef as RefObject<HTMLDivElement>, () => {
    setExpanded(false);
  });

  const { agents, isPending } = useSequentialCompatibleAgents();

  return (
    <div className={classes.root} ref={selectorRef}>
      <Button
        kind="ghost"
        size="md"
        className={classes.button}
        aria-haspopup="listbox"
        aria-controls={`${id}:options`}
        onClick={() => setExpanded(!expanded)}
        disabled={isDisabled}
      >
        <span>
          <Add size={20} />
        </span>
        Add an agent
      </Button>
      <ul className={classes.list} role="listbox" tabIndex={0} id={`${id}:options`} aria-expanded={expanded}>
        {!isPending ? (
          agents?.map((agent) => (
            <AgentListOption
              agent={agent}
              key={agent.name}
              onClick={() => {
                onSelectAgent(agent);
                setExpanded(false);
              }}
            />
          ))
        ) : (
          <SkeletonItems count={AGENTS_SKELETON_COUNT} render={(idx) => <AgentListOption.Skeleton key={idx} />} />
        )}
      </ul>
    </div>
  );
}

const AGENTS_SKELETON_COUNT = 4;
