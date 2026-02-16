/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Attribute } from 'keycloakify/login/KcContext';
import type { FormFieldError } from 'keycloakify/login/lib/useUserProfileForm';
import { Fragment } from 'react';

type FieldErrorsProps = {
  attribute: Attribute;
  displayableErrors: FormFieldError[];
  fieldIndex: number | undefined;
};

export function FieldErrors(props: FieldErrorsProps) {
  const { attribute, fieldIndex } = props;

  const displayableErrors = props.displayableErrors.filter((error) => error.fieldIndex === fieldIndex);

  if (displayableErrors.length === 0) {
    return null;
  }

  return (
    <span
      id={`input-error-${attribute.name}${fieldIndex === undefined ? '' : `-${fieldIndex}`}`}
      className="cds--form-requirement"
      aria-live="polite"
    >
      {displayableErrors
        .filter((error) => error.fieldIndex === fieldIndex)
        .map(({ errorMessage }, i, arr) => (
          <Fragment key={i}>
            {errorMessage}
            {arr.length - 1 !== i && <br />}
          </Fragment>
        ))}
    </span>
  );
}
