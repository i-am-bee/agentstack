/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Attribute } from "keycloakify/login/KcContext";
import type { FormFieldError } from "keycloakify/login/lib/useUserProfileForm";

import type { I18n } from "../../i18n";

export function getFieldError(
  displayableErrors: FormFieldError[],
  fieldIndex?: number,
): { hasError: boolean; errorMessage: string } {
  const errors = displayableErrors.filter(
    (error) => error.fieldIndex === fieldIndex,
  );
  const hasError = errors.length > 0;
  const errorMessage = errors
    .map(({ errorMessageStr }) => errorMessageStr)
    .join(", ");

  return { hasError, errorMessage };
}

export function getOptions(attribute: Attribute): string[] {
  const { inputOptionsFromValidation } = attribute.annotations;

  if (inputOptionsFromValidation !== undefined) {
    const validator = (
      attribute.validators as Record<string, { options?: string[] }>
    )[inputOptionsFromValidation];

    if (validator?.options !== undefined) {
      return validator.options;
    }
  }

  return attribute.validators.options?.options ?? [];
}

export function getInputLabel(
  i18n: I18n,
  attribute: Attribute,
  option: string,
): string {
  const { advancedMsgStr } = i18n;

  if (attribute.annotations.inputOptionLabels !== undefined) {
    const { inputOptionLabels } = attribute.annotations;
    return advancedMsgStr(inputOptionLabels[option] ?? option);
  }

  if (attribute.annotations.inputOptionLabelsI18nPrefix !== undefined) {
    return advancedMsgStr(
      `${attribute.annotations.inputOptionLabelsI18nPrefix}.${option}`,
    );
  }

  return option;
}
