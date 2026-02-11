/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import type { ToolCallApprovalRequest } from 'agentstack-sdk';
import { ApprovalDecision } from 'agentstack-sdk';
import isEmpty from 'lodash/isEmpty';
import { useCallback, useMemo, useState } from 'react';

import { Code } from '#components/MarkdownContent/components/Code.tsx';
import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageApproval } from '#modules/messages/utils.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';

import { FormLabel } from './FormLabel';
import classes from './MessageApproval.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function MessageApproval({ message }: Props) {
  const approvalPart = getMessageApproval(message);
  const { submitApproval } = useAgentRun();
  const { isLastMessage } = useMessages();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleDecision = useCallback(
    async (decision: ApprovalDecision) => {
      if (!approvalPart) {
        return;
      }

      setIsSubmitting(true);
      try {
        await submitApproval(decision, approvalPart.taskId);
      } finally {
        setIsSubmitting(false);
      }
    },
    [approvalPart, submitApproval],
  );

  const isCurrentMessageLast = isLastMessage(message);

  if (!approvalPart || !isCurrentMessageLast) {
    return null;
  }

  const { request } = approvalPart;
  const { title, action, description } = request;

  return (
    <div className={classes.root}>
      {action === 'tool-call' ? (
        <ToolCallContent request={request} />
      ) : (
        <>
          {title && <h3 className={classes.title}>{title}</h3>}
          {description && <p className={classes.description}>{description}</p>}
        </>
      )}

      {isCurrentMessageLast && (
        <div className={classes.actions}>
          <Button
            kind="tertiary"
            size="sm"
            onClick={() => handleDecision(ApprovalDecision.Reject)}
            disabled={isSubmitting}
          >
            Decline
          </Button>
          <Button
            kind="primary"
            size="sm"
            onClick={() => handleDecision(ApprovalDecision.Approve)}
            disabled={isSubmitting}
          >
            Allow
          </Button>
        </div>
      )}
    </div>
  );
}

function ToolCallContent({ request }: { request: ToolCallApprovalRequest }) {
  const { agent } = useAgentRun();

  const { title, name, input } = request;

  const requestInput = useMemo(() => (!isEmpty(input) ? JSON.stringify(input, null, 2) : null), [input]);

  return (
    <>
      <h3 className={classes.title}>{`${agent.name} wants to use ${title || name}`}</h3>
      {requestInput && (
        <div className={classes.toolCallInput}>
          <FormLabel>Request</FormLabel>
          <Code className="language-json">{requestInput}</Code>
        </div>
      )}
    </>
  );
}
