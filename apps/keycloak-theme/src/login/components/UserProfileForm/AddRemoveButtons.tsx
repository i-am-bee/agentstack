/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { Add, TrashCan } from '@carbon/react/icons';
import type { Attribute } from 'keycloakify/login/KcContext';
import type { FormAction } from 'keycloakify/login/lib/useUserProfileForm';
import { getButtonToDisplayForMultivaluedAttributeField } from 'keycloakify/login/lib/useUserProfileForm';

import type { I18n } from '../../i18n';
import classes from './AddRemoveButtons.module.scss';

type AddRemoveButtonsProps = {
  attribute: Attribute;
  values: string[];
  fieldIndex: number;
  dispatchFormAction: React.Dispatch<Extract<FormAction, { action: 'update' }>>;
  i18n: I18n;
};

export function AddRemoveButtons(props: AddRemoveButtonsProps) {
  const { attribute, values, fieldIndex, dispatchFormAction, i18n } = props;

  const { msg } = i18n;

  const { hasAdd, hasRemove } = getButtonToDisplayForMultivaluedAttributeField({
    attribute,
    values,
    fieldIndex,
  });

  const idPostfix = `-${attribute.name}-${fieldIndex + 1}`;

  if (!hasAdd && !hasRemove) {
    return null;
  }

  return (
    <div className={classes.root}>
      {hasRemove && (
        <Button
          id={`kc-remove${idPostfix}`}
          kind="ghost"
          size="sm"
          renderIcon={TrashCan}
          onClick={() =>
            dispatchFormAction({
              action: 'update',
              name: attribute.name,
              valueOrValues: values.filter((_, i) => i !== fieldIndex),
            })
          }
        >
          {msg('remove')}
        </Button>
      )}
      {hasAdd && (
        <Button
          id={`kc-add${idPostfix}`}
          kind="ghost"
          size="sm"
          renderIcon={Add}
          onClick={() =>
            dispatchFormAction({
              action: 'update',
              name: attribute.name,
              valueOrValues: [...values, ''],
            })
          }
        >
          {msg('addValue')}
        </Button>
      )}
    </div>
  );
}
