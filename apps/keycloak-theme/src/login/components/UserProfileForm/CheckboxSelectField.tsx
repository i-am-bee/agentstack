/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkbox, FormLabel } from "@carbon/react";

import classes from "./CheckboxSelectField.module.scss";
import { FieldLabel } from "./FieldLabel";
import type { InputFieldByTypeProps } from "./types";
import { getFieldError, getInputLabel, getOptions } from "./utils";

export function CheckboxSelectField(props: InputFieldByTypeProps) {
  const {
    attribute,
    dispatchFormAction,
    displayableErrors,
    i18n,
    valueOrValues,
  } = props;

  const { hasError, errorMessage } = getFieldError(displayableErrors);
  const options = getOptions(attribute);
  const values = valueOrValues as string[];

  return (
    <div className={classes.root}>
      <FormLabel>
        <FieldLabel i18n={i18n} attribute={attribute} />
      </FormLabel>
      <div className={classes.checkboxes}>
        {options.map((option) => (
          <Checkbox
            key={option}
            id={`${attribute.name}-${option}`}
            name={attribute.name}
            value={option}
            labelText={getInputLabel(i18n, attribute, option)}
            checked={values.includes(option)}
            invalid={hasError}
            invalidText={hasError ? errorMessage : undefined}
            disabled={attribute.readOnly}
            onChange={(_, { checked }) => {
              const newValues = [...values];
              if (checked) {
                newValues.push(option);
              } else {
                newValues.splice(newValues.indexOf(option), 1);
              }
              dispatchFormAction({
                action: "update",
                name: attribute.name,
                valueOrValues: newValues,
              });
            }}
            onBlur={() =>
              dispatchFormAction({
                action: "focus lost",
                name: attribute.name,
                fieldIndex: undefined,
              })
            }
          />
        ))}
      </div>
    </div>
  );
}
