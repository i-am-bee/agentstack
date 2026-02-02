/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Attribute } from 'keycloakify/login/KcContext';
import { assert } from 'keycloakify/tools/assert';

import type { I18n } from '../../i18n';
import classes from './GroupLabel.module.scss';

type GroupLabelProps = {
  attribute: Attribute;
  groupNameRef: {
    current: string;
  };
  i18n: I18n;
};

export function GroupLabel(props: GroupLabelProps) {
  const { attribute, groupNameRef, i18n } = props;

  const { advancedMsg } = i18n;

  if (attribute.group?.name !== groupNameRef.current) {
    groupNameRef.current = attribute.group?.name ?? '';

    if (groupNameRef.current !== '') {
      assert(attribute.group !== undefined);

      const groupDisplayHeader = attribute.group.displayHeader ?? '';
      const groupHeaderText = groupDisplayHeader !== '' ? advancedMsg(groupDisplayHeader) : attribute.group.name;

      const groupDisplayDescription = attribute.group.displayDescription ?? '';

      return (
        <div
          className={classes.group}
          {...Object.fromEntries(
            Object.entries(attribute.group.html5DataAnnotations).map(([key, value]) => [`data-${key}`, value]),
          )}
        >
          <h3 id={`header-${attribute.group.name}`} className={classes.header}>
            {groupHeaderText}
          </h3>
          {groupDisplayDescription !== '' && (
            <p id={`description-${attribute.group.name}`} className={classes.description}>
              {advancedMsg(groupDisplayDescription)}
            </p>
          )}
        </div>
      );
    }
  }

  return null;
}
