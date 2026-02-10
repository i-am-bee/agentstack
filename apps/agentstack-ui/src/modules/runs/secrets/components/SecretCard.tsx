/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import clsx from 'clsx';

import { useModal } from '#contexts/Modal/index.tsx';
import type { AgentSecret } from '#modules/runs/contexts/agent-secrets/types.ts';

import { useRevokeSecret } from '../hooks/useRevokeSecret';
import classes from './SecretCard.module.scss';
import { SecretsAddModal } from './SecretsAddModal';
import { SecretTag } from './SecretTag';

interface Props {
  secret: AgentSecret;
  variant?: 'default' | 'inline';
  onCloseAddModal?: () => void;
  onOpenAddModal?: () => void;
}

export function SecretCard({ secret, variant = 'default', onCloseAddModal, onOpenAddModal }: Props) {
  const { openModal } = useModal();
  const { revokeSecret } = useRevokeSecret();

  const openAddModal = () => {
    onOpenAddModal?.();

    openModal(({ onRequestClose, ...props }) => (
      <SecretsAddModal
        secret={secret}
        {...props}
        className={classes.addModal}
        onRequestClose={(force) => {
          onCloseAddModal?.();

          onRequestClose(force);
        }}
      />
    ));
  };

  const { name, description, isReady } = secret;

  return (
    <article className={clsx(classes.root, classes[`variant-${variant}`])}>
      <div className={classes.content}>
        <h3 className={classes.heading}>{name}</h3>

        <p className={classes.description}>{description}</p>

        <div className={classes.tag}>
          <SecretTag secret={secret} onClick={() => openAddModal()} size={variant === 'inline' ? 'md' : 'lg'} />
        </div>
      </div>

      {isReady && variant === 'inline' && (
        <OverflowMenu size="sm" flipped>
          <OverflowMenuItem itemText="Manage API Key" onClick={() => openAddModal()} />

          <OverflowMenuItem itemText="Revoke API Key" isDelete onClick={() => revokeSecret(secret)} />
        </OverflowMenu>
      )}
    </article>
  );
}
