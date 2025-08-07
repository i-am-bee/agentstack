/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckmarkFilled } from '@carbon/icons-react';
import { autoUpdate, flip, offset, useDismiss, useFloating, useInteractions, useRole } from '@floating-ui/react';
import { useCallback, useMemo, useState } from 'react';
import type { SubmitErrorHandler, SubmitHandler } from 'react-hook-form';
import { useForm } from 'react-hook-form';

import { useToast } from '#contexts/Toast/index.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';

import { useSendFeedback } from '../api/mutations/useSendFeedback';
import { createSendFeedbackPayload } from '../api/utils';
import { FEEDBACK_DIALOG_OFFSET, FEEDBACK_FORM_DEFAULTS } from '../constants';
import type { FeedbackForm } from '../types';
import { FeedbackVote } from '../types';

interface Props {
  message: UIAgentMessage;
  onOpenChange: (formOpen: boolean) => void;
}

export function useFeedback({ message, onOpenChange }: Props) {
  const [formOpen, setFormOpen] = useState(false);

  const { addToast } = useToast();
  const { mutateAsync: sendFeedback } = useSendFeedback();
  const { agent, contextId } = useAgentRun();

  const { refs, floatingStyles, context } = useFloating({
    placement: 'right-start',
    open: formOpen,
    onOpenChange: (nextOpen) => {
      if (nextOpen) {
        openForm();
      } else {
        closeForm();
      }
    },
    whileElementsMounted: autoUpdate,
    middleware: [offset(FEEDBACK_DIALOG_OFFSET), flip()],
  });

  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'dialog' });

  const { getReferenceProps, getFloatingProps } = useInteractions([dismiss, role]);

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
        await sendFeedback(createSendFeedbackPayload({ agent, message, values, contextId }));

        addToast({
          kind: 'info',
          title: 'Thank you for your feedback!',
          caption: undefined,
          icon: CheckmarkFilled,
          inlineIcon: true,
          timeout: 5_000,
        });

        if (shouldCloseFrom) {
          closeForm();
        }
      },
    [agent, message, contextId, sendFeedback, addToast, closeForm],
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
