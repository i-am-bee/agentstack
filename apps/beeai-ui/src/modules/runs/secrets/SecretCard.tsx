/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useCallback } from 'react';

import { useModal } from '#contexts/Modal/index.tsx';

import type { AgentSecret } from '../contexts/agent-secrets/types';
import classes from './SecretCard.module.scss';
import { SecretsAddModal } from './SecretsAddModal';
import { SecretTag } from './SecretTag';

interface Props {
  secret: AgentSecret;
  variant?: 'default' | 'inline';
  updateSecret: (key: string, value: string) => void;
  onCloseAddModal?: () => void;
  onOpenAddModal?: () => void;
}

export function SecretCard({ secret, variant = 'default', onCloseAddModal, onOpenAddModal, updateSecret }: Props) {
  const { openModal } = useModal();

  const openAddModal = useCallback(() => {
    onOpenAddModal?.();

    openModal(({ onRequestClose, ...props }) => (
      <SecretsAddModal
        secret={secret}
        {...props}
        updateSecret={updateSecret}
        className={classes.addModal}
        onRequestClose={(force) => {
          onCloseAddModal?.();

          onRequestClose(force);
        }}
      />
    ));
  }, [onOpenAddModal, openModal, secret, updateSecret, onCloseAddModal]);

  const { name, description } = secret;

  return (
    <article className={clsx(classes.root, classes[`variant-${variant}`])}>
      <h3 className={classes.heading}>{name}</h3>

      <p className={classes.description}>{description}</p>

      <div className={classes.tag}>
        <SecretTag secret={secret} onClick={() => openAddModal()} size={variant === 'inline' ? 'md' : 'lg'} />
      </div>
    </article>
  );
}
