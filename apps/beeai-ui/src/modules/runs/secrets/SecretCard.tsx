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
    <article className={classes.root}>
      <h3 className={classes.heading}>{name}</h3>

      <p className={classes.description}>{description}</p>

      <div className={classes.tag}>
        <SecretTag secret={secret} onClick={() => openAddModal()} />
      </div>
    </article>
  );
}
