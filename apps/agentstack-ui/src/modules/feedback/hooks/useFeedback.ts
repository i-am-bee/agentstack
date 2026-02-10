/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckmarkFilled } from '@carbon/icons-react';
import { useMemo, useState } from 'react';
import type { SubmitErrorHandler, SubmitHandler } from 'react-hook-form';
import { useForm } from 'react-hook-form';

import { getErrorMessage } from '#api/utils.ts';
import { useToast } from '#contexts/Toast/index.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';

import { useSendFeedback } from '../api/mutations/useSendFeedback';
import { createSendFeedbackPayload } from '../api/utils';
import { FEEDBACK_FORM_DEFAULTS } from '../constants';
import type { FeedbackForm } from '../types';
import { FeedbackVote } from '../types';
import { useFeedbackDialog } from './useFeedbackDialog';

interface Props {
  message: UIAgentMessage;
  onOpenChange: (formOpen: boolean) => void;
}

export function useFeedback({ message, onOpenChange }: Props) {
  const [formOpen, setFormOpen] = useState(false);

  const { addToast } = useToast();
  const { mutateAsync: sendFeedback } = useSendFeedback();
  const { agent } = useAgentRun();
  const { getContextId } = usePlatformContext();
  const { refs, floatingStyles, getReferenceProps, getFloatingProps } = useFeedbackDialog({
    open: formOpen,
    onOpenChange: (nextOpen) => {
      if (nextOpen) {
        openForm();
      } else {
        closeForm();
      }
    },
  });

  const form = useForm<FeedbackForm>({
    defaultValues: FEEDBACK_FORM_DEFAULTS,
    mode: 'onChange',
  });
  const { getValues, reset, handleSubmit } = form;

  const currentVote = getValues('vote');

  const openForm = () => {
    setFormOpen(true);
    onOpenChange(true);
  };

  const closeForm = () => {
    setFormOpen(false);
    onOpenChange(false);
    reset();
  };
  const onSubmit: (params?: { shouldCloseFrom?: boolean }) => SubmitHandler<FeedbackForm> =
    ({ shouldCloseFrom } = {}) =>
    async (values) => {
      const contextId = getContextId();

      try {
        await sendFeedback(createSendFeedbackPayload({ agent, message, values, contextId }));

        addToast({
          title: 'Thank you for your feedback!',
          icon: CheckmarkFilled,
          timeout: 5_000,
          hideDate: true,
        });
      } catch (error) {
        addToast({
          kind: 'error',
          title: 'Failed to send feedback',
          message: getErrorMessage(error) || 'An unknown error occurred',
        });
      }

      if (shouldCloseFrom) {
        closeForm();
      }
    };
  const onError: SubmitErrorHandler<FeedbackForm> = (errors) => {
    const errorMessages = Object.values(errors).map(({ message }) => message);

    addToast({
      kind: 'error',
      title: 'Form contains errors',
      message: errorMessages.join('\n'),
    });
  };
  const handleVote = (vote: FeedbackVote) => {
    if (currentVote !== vote) {
      reset({ ...FEEDBACK_FORM_DEFAULTS, vote });
    }

    if (vote === FeedbackVote.Up) {
      handleSubmit(onSubmit(), onError)();
    } else {
      openForm();
    }
  };

  const getVoteUpProps = () => ({
    onClick: () => handleVote(FeedbackVote.Up),
  });

  const getVoteDownProps = () => ({
    ...getReferenceProps({
      onClick: () => handleVote(FeedbackVote.Down),
    }),
  });

  const getDialogProps = () => ({
    ref: refs.setFloating,
    style: floatingStyles,
    ...getFloatingProps(),
  });

  const getFormProps = () => ({
    form,
    onSubmit: handleSubmit(onSubmit({ shouldCloseFrom: true }), onError),
    onCloseClick: closeForm,
  });

  const positionRef = useMemo(() => refs.setReference, [refs.setReference]);

  return {
    formOpen,
    currentVote,
    getVoteUpProps,
    getVoteDownProps,
    getDialogProps,
    getFormProps,
    positionRef,
  };
}
