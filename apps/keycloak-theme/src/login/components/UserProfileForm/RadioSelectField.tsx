/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FormLabel, RadioButton, RadioButtonGroup } from '@carbon/react';

import { FieldLabel } from './FieldLabel';
import type { InputFieldByTypeProps } from './types';
import { getFieldError, getInputLabel, getOptions } from './utils';

export function RadioSelectField(props: InputFieldByTypeProps) {
  const { attribute, dispatchFormAction, displayableErrors, i18n, valueOrValues } = props;

  const { hasError, errorMessage } = getFieldError(displayableErrors);
  const options = getOptions(attribute);

  return (
    <div>
      <FormLabel>
        <FieldLabel i18n={i18n} attribute={attribute} />
      </FormLabel>
      <RadioButtonGroup
        name={attribute.name}
        valueSelected={valueOrValues as string}
        invalid={hasError}
        invalidText={errorMessage}
        disabled={attribute.readOnly}
        onChange={(value) =>
          dispatchFormAction({
            action: 'update',
            name: attribute.name,
            valueOrValues: value as string,
          })
        }
        onBlur={() =>
          dispatchFormAction({
            action: 'focus lost',
            name: attribute.name,
            fieldIndex: undefined,
          })
        }
      >
        {options.map((option) => (
          <RadioButton
            key={option}
            id={`${attribute.name}-${option}`}
            value={option}
            labelText={getInputLabel(i18n, attribute, option)}
          />
        ))}
      </RadioButtonGroup>
    </div>
  );
}
