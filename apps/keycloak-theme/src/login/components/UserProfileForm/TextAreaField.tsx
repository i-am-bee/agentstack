/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextArea } from '@carbon/react';
import { assert } from 'keycloakify/tools/assert';

import { FieldLabel } from './FieldLabel';
import type { InputFieldByTypeProps } from './types';
import { getFieldError } from './utils';

export function TextAreaField(props: InputFieldByTypeProps) {
  const { attribute, dispatchFormAction, displayableErrors, valueOrValues, i18n } = props;

  assert(typeof valueOrValues === 'string');
  const value = valueOrValues;

  const { hasError, errorMessage } = getFieldError(displayableErrors);

  return (
    <TextArea
      id={attribute.name}
      name={attribute.name}
      value={value}
      labelText={<FieldLabel i18n={i18n} attribute={attribute} />}
      invalid={hasError}
      invalidText={errorMessage}
      disabled={attribute.readOnly}
      rows={
        attribute.annotations.inputTypeRows === undefined
          ? undefined
          : parseInt(`${attribute.annotations.inputTypeRows}`)
      }
      maxLength={
        attribute.annotations.inputTypeMaxlength === undefined
          ? undefined
          : parseInt(`${attribute.annotations.inputTypeMaxlength}`)
      }
      onChange={(event) =>
        dispatchFormAction({
          action: 'update',
          name: attribute.name,
          valueOrValues: event.target.value,
        })
      }
      onBlur={() =>
        dispatchFormAction({
          action: 'focus lost',
          name: attribute.name,
          fieldIndex: undefined,
        })
      }
    />
  );
}
