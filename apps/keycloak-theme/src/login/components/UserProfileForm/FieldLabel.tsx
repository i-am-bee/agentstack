/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Attribute } from 'keycloakify/login/KcContext';

import type { I18n } from '../../i18n';

type FieldLabelProps = {
  i18n: I18n;
  attribute: Attribute;
};

export function FieldLabel({ i18n, attribute }: FieldLabelProps) {
  const { advancedMsg } = i18n;

  return (
    <>
      {advancedMsg(attribute.displayName ?? '')}
      {attribute.required && ' *'}
    </>
  );
}
