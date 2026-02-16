/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Attribute } from 'keycloakify/login/KcContext';
import type { FormAction, FormFieldError } from 'keycloakify/login/lib/useUserProfileForm';

import type { I18n } from '../../i18n';

export type InputFieldByTypeProps = {
  attribute: Attribute;
  valueOrValues: string | string[];
  displayableErrors: FormFieldError[];
  dispatchFormAction: React.Dispatch<FormAction>;
  i18n: I18n;
};
