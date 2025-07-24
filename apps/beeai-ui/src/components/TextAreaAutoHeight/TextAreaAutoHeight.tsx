/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { ChangeEvent, CSSProperties, TextareaHTMLAttributes } from 'react';
import { forwardRef, useCallback, useEffect, useRef, useState } from 'react';
import { mergeRefs } from 'react-merge-refs';
import { Resizable } from 'react-resizable';

import classes from './TextAreaAutoHeight.module.scss';

type Props = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'value'> & {
  maxRows?: number;
  resizable?: boolean;
};

export const TextAreaAutoHeight = forwardRef<HTMLTextAreaElement, Props>(function TextAreaAutoHeight(
  { className, resizable, maxRows, onChange, ...rest },
  ref,
) {
  const [value, setValue] = useState(rest.defaultValue ?? '');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [manualHeight, setManualHeight] = useState<number | null>(null);

  const handleInput = useCallback((event: Event) => {
    setValue((event.target as HTMLTextAreaElement).value);
  }, []);

  const updateOverflowValue = useCallback(() => {
    if (textareaRef.current && containerRef.current) {
      textareaRef.current.style.overflow =
        textareaRef.current?.scrollHeight > containerRef.current?.scrollHeight ? 'auto' : 'hidden';
    }
  }, []);

  const handleChange = useCallback(
    (event: ChangeEvent<HTMLTextAreaElement>) => {
      onChange?.(event);

      updateOverflowValue();
    },
    [onChange, updateOverflowValue],
  );

  useEffect(() => {
    updateOverflowValue();
  }, [updateOverflowValue]);

  // This is necessary for the auto height to work properly. React does some optimization and ignores custom Event dispatch
  //  if the value is unchanged, which happens with react-hook-form.
  useEffect(() => {
    const element = textareaRef.current;

    element?.addEventListener('input', handleInput);

    return () => element?.removeEventListener('input', handleInput);
  });

  const content = (
    <div
      ref={containerRef}
      className={clsx(classes.root, className, {
        [classes.resizable]: resizable,
        [classes.resized]: Boolean(manualHeight),
      })}
      data-replicated-value={value}
      style={maxRows ? ({ '--max-rows': `${maxRows}` } as CSSProperties) : undefined}
    >
      <textarea ref={mergeRefs([ref, textareaRef])} {...rest} onChange={handleChange} />
    </div>
  );

  return resizable ? (
    <Resizable
      width={10}
      height={manualHeight ?? 0}
      onResizeStart={() => setManualHeight(textareaRef.current?.offsetHeight ?? 0)}
      onResize={(_, data) => {
        const newHeight = data.size.height;
        setManualHeight(newHeight);
        if (textareaRef.current) textareaRef.current.style.blockSize = `${newHeight}px`;
      }}
      handle={
        <button className={classes.resizeHandle}>
          <span className={classes.resizeHandleContent}></span>
        </button>
      }
    >
      {content}
    </Resizable>
  ) : (
    content
  );
});
