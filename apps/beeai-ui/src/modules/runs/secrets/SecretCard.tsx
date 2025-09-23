/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Tools } from '@carbon/icons-react';
import { useCallback } from 'react';

import { useModal } from '#contexts/Modal/index.tsx';

import type { AgentSecret } from '../contexts/agent-secrets/types';
import classes from './SecretCard.module.scss';
import { SecretsAddModal } from './SecretsAddModal';
import { SecretTag } from './SecretTag';

interface Props {
  secret: AgentSecret;
  updateSecret: (key: string, value: string) => void;
  onCloseAddModal?: () => void;
  onOpenAddModal?: () => void;
}

export function SecretCard({ secret, onCloseAddModal, onOpenAddModal, updateSecret }: Props) {
  const { openModal } = useModal();

  const openAddModal = useCallback(() => {
    onOpenAddModal?.();

    openModal(({ onRequestClose, ...props }) => (
      <SecretsAddModal
        secret={secret} // TODO: pass the actual secret here
        {...props}
        updateSecret={updateSecret}
        onRequestClose={(force) => {
          onCloseAddModal?.();

          onRequestClose(force);
        }}
      />
    ));
  }, [onOpenAddModal, openModal, secret, updateSecret, onCloseAddModal]);

  return (
    <article className={classes.root}>
      <span className={classes.icon}>
        <Tools size={32} />
      </span>

      <h3 className={classes.heading}>Outlook</h3>

      <p className={classes.description}>
        Advanced reasoning and analysis to provide thoughtful, well-structured responses to complex questions and
        topics, lorem ipsum dolor sit amet...
      </p>

      <div className={classes.tag}>
        <SecretTag secret={secret} onClick={() => openAddModal()} />
      </div>
    </article>
  );
}
