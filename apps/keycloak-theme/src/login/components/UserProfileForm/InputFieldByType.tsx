/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckboxSelectField } from './CheckboxSelectField';
import { InputField } from './InputField';
import { PasswordField } from './PasswordField';
import { RadioSelectField } from './RadioSelectField';
import { SelectField } from './SelectField';
import { TextAreaField } from './TextAreaField';
import type { InputFieldByTypeProps } from './types';

export function InputFieldByType(props: InputFieldByTypeProps) {
  const { attribute, valueOrValues } = props;

  switch (attribute.annotations.inputType) {
    case 'hidden':
      return <input type="hidden" name={attribute.name} value={valueOrValues} />;
    case 'textarea':
      return <TextAreaField {...props} />;
    case 'select':
    case 'multiselect':
      return <SelectField {...props} />;
    case 'select-radiobuttons':
      return <RadioSelectField {...props} />;
    case 'multiselect-checkboxes':
      return <CheckboxSelectField {...props} />;
    default: {
      if (valueOrValues instanceof Array) {
        return (
          <>
            {valueOrValues.map((_, i) => (
              <InputField key={i} {...props} fieldIndex={i} />
            ))}
          </>
        );
      }

      // Password fields
      if (attribute.name === 'password' || attribute.name === 'password-confirm') {
        return <PasswordField {...props} fieldIndex={undefined} />;
      }

      return <InputField {...props} fieldIndex={undefined} />;
    }
  }
}
