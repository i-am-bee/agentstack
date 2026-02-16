/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useUserProfileForm } from 'keycloakify/login/lib/useUserProfileForm';
import type { UserProfileFormFieldsProps } from 'keycloakify/login/UserProfileFormFieldsProps';
import { Fragment, useEffect } from 'react';

import type { I18n } from '../../i18n';
import type { KcContext } from '../../KcContext';
import { FieldErrors } from './FieldErrors';
import { GroupLabel } from './GroupLabel';
import { InputFieldByType } from './InputFieldByType';
import classes from './UserProfileFormFields.module.scss';

export default function UserProfileFormFields({
  kcContext,
  i18n,
  onIsFormSubmittableValueChange,
  doMakeUserConfirmPassword,
  BeforeField,
  AfterField,
}: UserProfileFormFieldsProps<KcContext, I18n>) {
  const {
    formState: { formFieldStates, isFormSubmittable },
    dispatchFormAction,
  } = useUserProfileForm({
    kcContext,
    i18n,
    doMakeUserConfirmPassword,
  });

  useEffect(() => {
    onIsFormSubmittableValueChange(isFormSubmittable);
  }, [isFormSubmittable]);

  const groupNameRef = { current: '' };

  return (
    <div className={classes.root}>
      {formFieldStates.map(({ attribute, displayableErrors, valueOrValues }) => {
        const isHidden =
          attribute.annotations.inputType === 'hidden' ||
          (attribute.name === 'password-confirm' && !doMakeUserConfirmPassword);

        return (
          <Fragment key={attribute.name}>
            <GroupLabel attribute={attribute} groupNameRef={groupNameRef} i18n={i18n} />
            {BeforeField !== undefined && (
              <BeforeField
                attribute={attribute}
                dispatchFormAction={dispatchFormAction}
                displayableErrors={displayableErrors}
                valueOrValues={valueOrValues}
                kcClsx={() => ''}
                i18n={i18n}
              />
            )}
            <div className={classes.field} style={{ display: isHidden ? 'none' : undefined }}>
              <InputFieldByType
                attribute={attribute}
                valueOrValues={valueOrValues}
                displayableErrors={displayableErrors}
                dispatchFormAction={dispatchFormAction}
                i18n={i18n}
              />
              {/* Only show separate FieldErrors for non-multi-valued fields */}
              {!(valueOrValues instanceof Array) && (
                <FieldErrors attribute={attribute} displayableErrors={displayableErrors} fieldIndex={undefined} />
              )}
            </div>
            {AfterField !== undefined && (
              <AfterField
                attribute={attribute}
                dispatchFormAction={dispatchFormAction}
                displayableErrors={displayableErrors}
                valueOrValues={valueOrValues}
                kcClsx={() => ''}
                i18n={i18n}
              />
            )}
          </Fragment>
        );
      })}
    </div>
  );
}
