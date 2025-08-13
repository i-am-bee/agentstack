/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, PasswordInput } from '@carbon/react';
import clsx from 'clsx';
import { useId } from 'react';

import classes from './AddApiKeyForm.module.scss';

interface Props {
  toolName: string;
  variant: AddApiKeyFormVariant;
  onDeleteClick?: () => void;
}

export function AddApiKeyForm({ toolName, variant, onDeleteClick }: Props) {
  const id = useId();

  const isInlineVariant = variant === AddApiKeyFormVariant.Inline;
  const inputLabel = isInlineVariant ? `${toolName} API Key` : 'API Key';
  const buttonLabel = isInlineVariant ? 'Submit' : 'Continue';

  return (
    <form className={clsx(classes.root, classes[`is-${variant}`])}>
      {isInlineVariant && (
        <p className={classes.description}>
          Sure thing, but before I can access {toolName}, I will need you to provide your API&nbsp;Key.
        </p>
      )}

      <div className={classes.group}>
        {onDeleteClick && (
          <Button kind="ghost" className={classes.delete} onClick={onDeleteClick}>
            Delete key
          </Button>
        )}

        <PasswordInput
          id={`${id}:api-key`}
          size="lg"
          labelText={inputLabel}
          autoFocus
          showPasswordLabel="Show API Key"
          hidePasswordLabel="Hide API Key"
        />
      </div>

      <Button className={classes.button} disabled>
        {buttonLabel}
      </Button>
    </form>
  );
}

export enum AddApiKeyFormVariant {
  Modal = 'modal',
  Inline = 'inline',
}
