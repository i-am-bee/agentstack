/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Close } from '@carbon/icons-react';
import { Button, IconButton, OperationalTag, TextArea } from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useId, useMemo } from 'react';
import type { UseFormReturn } from 'react-hook-form';

import { FEEDBACK_CATEGORIES } from '../constants';
import type { FeedbackCategory, FeedbackForm } from '../types';
import classes from './FeedbackForm.module.scss';

interface Props {
  form: UseFormReturn<FeedbackForm>;
  onCloseClick: () => void;
  onSubmit: () => void;
}

export function FeedbackForm({ form, onCloseClick, onSubmit }: Props) {
  const id = useId();
  const {
    formState: { isSubmitting },
    register,
  } = form;

  return (
    <div className={classes.root}>
      <header className={classes.header}>
        <h2 className={classes.heading}>How can I improve?</h2>

        <IconButton kind="ghost" size="sm" label="Close" onClick={onCloseClick}>
          <Close />
        </IconButton>
      </header>

      <form className={classes.form} onSubmit={onSubmit}>
        <ul className={classes.categories}>
          {FEEDBACK_CATEGORIES.map((category) => (
            <FeedbackCategory key={category.id} category={category} form={form} />
          ))}
        </ul>

        <TextArea
          className={classes.comment}
          id={`${id}:comment`}
          labelText="Comments"
          placeholder="Add more details on what went wrong and how the answer could be improved"
          rows={4}
          autoFocus
          {...register('comment')}
        />

        <div className={classes.submit}>
          <Button type="submit" size="sm" disabled={isSubmitting}>
            Submit
          </Button>
        </div>
      </form>
    </div>
  );
}

interface FeedbackCategoryProps {
  category: FeedbackCategory;
  form: UseFormReturn<FeedbackForm>;
}

function FeedbackCategory({ category, form }: FeedbackCategoryProps) {
  const { label } = category;
  const { watch, setValue } = form;

  const categories = watch('categories');
  const value = useMemo(() => categories ?? [], [categories]);

  const isSelected = useMemo(() => value.some(({ id }) => id === category.id), [value, category]);

  const handleClick = useCallback(() => {
    const newValue = isSelected ? value.filter(({ id }) => id !== category.id) : [...value, category];

    setValue('categories', newValue, { shouldDirty: true });
  }, [isSelected, value, category, setValue]);

  return (
    <li>
      <OperationalTag
        text={label}
        className={clsx(classes.category, { [classes.isSelected]: isSelected })}
        onClick={handleClick}
      />
    </li>
  );
}
