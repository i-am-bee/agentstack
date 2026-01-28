/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { PasswordInput } from "@carbon/react";
import { assert } from "keycloakify/tools/assert";

import { FieldLabel } from "./FieldLabel";
import type { InputFieldByTypeProps } from "./types";
import { getFieldError } from "./utils";

type PasswordFieldProps = InputFieldByTypeProps & {
  fieldIndex: number | undefined;
};

export function PasswordField(props: PasswordFieldProps) {
  const {
    attribute,
    fieldIndex,
    dispatchFormAction,
    valueOrValues,
    i18n,
    displayableErrors,
  } = props;

  const { advancedMsgStr, msgStr } = i18n;

  const { hasError, errorMessage } = getFieldError(
    displayableErrors,
    fieldIndex,
  );

  const value = (() => {
    if (fieldIndex !== undefined) {
      assert(valueOrValues instanceof Array);
      return valueOrValues[fieldIndex];
    }
    assert(typeof valueOrValues === "string");
    return valueOrValues;
  })();

  return (
    <PasswordInput
      id={attribute.name}
      name={attribute.name}
      value={value}
      labelText={<FieldLabel i18n={i18n} attribute={attribute} />}
      invalid={hasError}
      invalidText={errorMessage}
      disabled={attribute.readOnly}
      autoComplete={attribute.autocomplete}
      placeholder={
        attribute.annotations.inputTypePlaceholder === undefined
          ? undefined
          : advancedMsgStr(attribute.annotations.inputTypePlaceholder)
      }
      hidePasswordLabel={msgStr("hidePassword")}
      showPasswordLabel={msgStr("showPassword")}
      {...Object.fromEntries(
        Object.entries(attribute.html5DataAnnotations ?? {}).map(
          ([key, value]) => [`data-${key}`, value],
        ),
      )}
      onChange={(event) =>
        dispatchFormAction({
          action: "update",
          name: attribute.name,
          valueOrValues: (() => {
            if (fieldIndex !== undefined) {
              assert(valueOrValues instanceof Array);
              return valueOrValues.map((v, i) =>
                i === fieldIndex ? event.target.value : v,
              );
            }
            return event.target.value;
          })(),
        })
      }
      onBlur={() =>
        dispatchFormAction({
          action: "focus lost",
          name: attribute.name,
          fieldIndex: fieldIndex,
        })
      }
    />
  );
}
