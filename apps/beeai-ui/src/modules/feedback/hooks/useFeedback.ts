/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckmarkFilled } from '@carbon/icons-react';
import { useCallback, useMemo, useState } from 'react';
import type { SubmitErrorHandler, SubmitHandler } from 'react-hook-form';
import { useForm } from 'react-hook-form';

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

  const openForm = useCallback(() => {
    setFormOpen(true);
    onOpenChange(true);
  }, [onOpenChange]);

  const closeForm = useCallback(() => {
    setFormOpen(false);
    onOpenChange(false);
    reset();
  }, [onOpenChange, reset]);

  const onSubmit: (params?: { shouldCloseFrom?: boolean }) => SubmitHandler<FeedbackForm> = useCallback(
    ({ shouldCloseFrom } = {}) =>
      async (values) => {
        const contextId = getContextId();

        try {
          await sendFeedback(createSendFeedbackPayload({ agent, message, values, contextId }));

          addToast({
            kind: 'info',
            title: 'Thank you for your feedback!',
            hideTimeElapsed: true,
            icon: CheckmarkFilled,
            inlineIcon: true,
            timeout: 5_000,
          });
        } catch (error) {
          addToast({
            kind: 'error',
            title: 'Failed to send feedback',
            subtitle: error instanceof Error ? error.message : 'An unknown error occurred',
          });
        }

        if (shouldCloseFrom) {
          closeForm();
        }
      },
    [addToast, agent, closeForm, getContextId, message, sendFeedback],
  );

  const onError: SubmitErrorHandler<FeedbackForm> = useCallback(
    (errors) => {
      const errorMessages = Object.values(errors).map(({ message }) => message);

      addToast({
        title: 'Form contains errors',
        subtitle: errorMessages.join('\n'),
      });
    },
    [addToast],
  );

  const handleVote = useCallback(
    (vote: FeedbackVote) => {
      if (currentVote !== vote) {
        reset({ ...FEEDBACK_FORM_DEFAULTS, vote });
      }

      if (vote === FeedbackVote.Up) {
        handleSubmit(onSubmit(), onError)();
      } else {
        openForm();
      }
    },
    [currentVote, reset, handleSubmit, onSubmit, onError, openForm],
  );

  const getVoteUpProps = useCallback(
    () => ({
      onClick: () => handleVote(FeedbackVote.Up),
    }),
    [handleVote],
  );

  const getVoteDownProps = useCallback(
    () => ({
      ...getReferenceProps({
        onClick: () => handleVote(FeedbackVote.Down),
      }),
    }),
    [handleVote, getReferenceProps],
  );

  const getDialogProps = useCallback(
    () => ({
      ref: refs.setFloating,
      style: floatingStyles,
      ...getFloatingProps(),
    }),
    [refs.setFloating, floatingStyles, getFloatingProps],
  );

  const getFormProps = useCallback(
    () => ({
      form,
      onSubmit: handleSubmit(onSubmit({ shouldCloseFrom: true }), onError),
      onCloseClick: closeForm,
    }),
    [form, handleSubmit, onSubmit, onError, closeForm],
  );

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
