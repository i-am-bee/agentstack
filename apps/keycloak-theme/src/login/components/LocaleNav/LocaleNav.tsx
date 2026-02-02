/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Dropdown } from "@carbon/react";
import { useId } from "react";

import type { I18n } from "../../i18n";
import classes from "./LocaleNav.module.scss";

interface Props {
  i18n: I18n;
}

export function LocaleNav({ i18n }: Props) {
  const id = useId();
  const { enabledLanguages, currentLanguage } = i18n;

  if (enabledLanguages.length <= 1 || !currentLanguage) {
    return null;
  }

  const items = enabledLanguages.map(({ languageTag, label }) => ({
    id: languageTag,
    label: label,
  }));

  const handleChange = ({
    selectedItem,
  }: {
    selectedItem: { id: string; label: string };
  }) => {
    const language = enabledLanguages.find(
      (lang) => lang.languageTag === selectedItem.id,
    );
    if (language?.href) {
      window.location.href = language.href;
    }
  };

  const { label, languageTag } = currentLanguage;

  return (
    <Dropdown
      className={classes.dropdown}
      id={id}
      titleText="Switch Language"
      label={label}
      size="sm"
      items={items}
      itemToString={(item) => item?.label ?? ""}
      selectedItem={currentLanguage ? { id: languageTag, label } : undefined}
      onChange={handleChange}
    />
  );
}
