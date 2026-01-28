/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Dropdown, FilterableMultiSelect } from "@carbon/react";

import { FieldLabel } from "./FieldLabel";
import type { InputFieldByTypeProps } from "./types";
import { getFieldError, getInputLabel, getOptions } from "./utils";

export function SelectField(props: InputFieldByTypeProps) {
  const {
    attribute,
    dispatchFormAction,
    displayableErrors,
    i18n,
    valueOrValues,
  } = props;

  const isMultiple = attribute.annotations.inputType === "multiselect";
  const { hasError, errorMessage } = getFieldError(displayableErrors);

  const options = getOptions(attribute);
  const items = options.map((option) => ({
    id: option,
    label: getInputLabel(i18n, attribute, option),
  }));

  if (isMultiple) {
    const selectedItems = items.filter((item) =>
      (valueOrValues as string[]).includes(item.id),
    );

    return (
      <>
        <FilterableMultiSelect
          id={attribute.name}
          titleText={<FieldLabel i18n={i18n} attribute={attribute} />}
          items={items}
          itemToString={(item) => item?.label ?? ""}
          initialSelectedItems={selectedItems}
          invalid={hasError}
          invalidText={errorMessage}
          disabled={attribute.readOnly}
          onChange={({ selectedItems }) =>
            dispatchFormAction({
              action: "update",
              name: attribute.name,
              valueOrValues: selectedItems.map((item) => item.id),
            })
          }
          onMenuChange={() =>
            dispatchFormAction({
              action: "focus lost",
              name: attribute.name,
              fieldIndex: undefined,
            })
          }
        />
        {(valueOrValues as string[]).map((value, index) => (
          <input
            key={index}
            type="hidden"
            name={attribute.name}
            value={value}
          />
        ))}
      </>
    );
  }

  const selectedItem = items.find((item) => item.id === valueOrValues) ?? null;

  return (
    <>
      <Dropdown
        id={attribute.name}
        label="Select..."
        titleText={<FieldLabel i18n={i18n} attribute={attribute} />}
        items={items}
        itemToString={(item) => item?.label ?? ""}
        selectedItem={selectedItem}
        invalid={hasError}
        invalidText={errorMessage}
        disabled={attribute.readOnly}
        onChange={({ selectedItem }) =>
          dispatchFormAction({
            action: "update",
            name: attribute.name,
            valueOrValues: selectedItem?.id ?? "",
          })
        }
      />
      <input
        type="hidden"
        name={attribute.name}
        value={valueOrValues as string}
      />
    </>
  );
}
