/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  autoUpdate,
  flip,
  FloatingPortal,
  offset,
  useClick,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
} from '@floating-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import debounce from 'lodash/debounce';
import type { Dispatch, RefObject, SetStateAction } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import { fadeProps } from '#utils/fadeProps.ts';

import classes from './PromptSuggestions.module.scss';

interface Props {
  inputRef: RefObject<HTMLTextAreaElement | null>;
  isOpen: boolean;
  suggestions: string[];
  setIsOpen: Dispatch<SetStateAction<boolean>>;
  onSubmit: (input: string) => void;
}

export function PromptSuggestions({ inputRef, isOpen, suggestions, setIsOpen, onSubmit }: Props) {
  const { refs, floatingStyles, context, placement } = useFloating({
    placement: 'bottom-start',
    open: isOpen,
    onOpenChange: setIsOpen,
    whileElementsMounted: autoUpdate,
    middleware: [offset(OFFSET), flip()],
  });

  const click = useClick(context);
  const dismiss = useDismiss(context, {
    outsidePress: (event) => event.target !== inputRef.current,
  });
  const role = useRole(context, { role: 'dialog' });

  const { getReferenceProps, getFloatingProps } = useInteractions([click, dismiss, role]);

  const handleInputClick = (event: MouseEvent) => {
    if (isOpen) {
      return;
    }

    const target = event.target as HTMLTextAreaElement;

    if (target.value === '') {
      setIsOpen(true);
    }
  };

  const handleInputKeyUp = (event: KeyboardEvent) => {
    if (!isOpen) {
      return;
    }

    const target = event.target as HTMLTextAreaElement;

    if (target.value.length > 0) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    const inputElement = inputRef.current;

    inputElement?.addEventListener('click', handleInputClick);
    inputElement?.addEventListener('keyup', handleInputKeyUp);

    return () => {
      inputElement?.removeEventListener('click', handleInputClick);
      inputElement?.removeEventListener('keyup', handleInputKeyUp);
    };
  });

  const visibleSuggestions = useMemo(() => suggestions.slice(0, ITEMS_MAX_LENGTH), [suggestions]);

  if (!suggestions.length) {
    return;
  }

  return (
    <>
      <div ref={refs.setReference} className={classes.ref} {...getReferenceProps()} />

      <AnimatePresence>
        {isOpen && (
          <FloatingPortal>
            <div ref={refs.setFloating} style={floatingStyles} {...getFloatingProps()}>
              <Container size="md" className={classes.root}>
                <motion.div
                  {...fadeProps({
                    hidden: {
                      transform: placement === 'bottom-start' ? 'translateY(-1rem)' : 'translateY(1rem)',
                    },
                    visible: {
                      transform: 'translateY(0)',
                    },
                  })}
                >
                  <div className={classes.content}>
                    <h3 className={classes.heading}>Suggested</h3>

                    <ul className={classes.list}>
                      {visibleSuggestions.map((prompt, idx) => (
                        <li key={idx} className={classes.item}>
                          <SuggestionButton content={prompt} onSubmit={onSubmit} />
                        </li>
                      ))}
                    </ul>
                  </div>
                </motion.div>
              </Container>
            </div>
          </FloatingPortal>
        )}
      </AnimatePresence>
    </>
  );
}

function SuggestionButton({ content, onSubmit }: { content: string; onSubmit: (input: string) => void }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [isTruncated, setIsTruncated] = useState(false);

  const checkOverflow = useCallback(() => {
    const element = ref.current;

    if (!element) {
      return;
    }

    const { scrollHeight, clientHeight } = element;

    if (scrollHeight > clientHeight) {
      setIsTruncated(true);
    } else {
      setIsTruncated(false);
    }
  }, []);

  const debouncedCheckOverflow = useMemo(() => debounce(checkOverflow, 200), [checkOverflow]);

  useEffect(() => {
    const element = ref.current;

    if (!element) {
      return;
    }

    const resizeObserver = new ResizeObserver(() => {
      debouncedCheckOverflow();
    });

    resizeObserver.observe(element);
    checkOverflow();

    return () => {
      if (element) {
        resizeObserver.unobserve(element);
      }
    };
  }, [checkOverflow, debouncedCheckOverflow, isTruncated]);

  const buttonContent = (
    <button className={classes.button} type="button" onClick={() => onSubmit(content)}>
      <span ref={ref}>{content}</span>
    </button>
  );

  return isTruncated ? (
    <Tooltip content={content} placement="top" asChild>
      {buttonContent}
    </Tooltip>
  ) : (
    buttonContent
  );
}

const OFFSET = {
  mainAxis: 27, // Space between the input and the suggestions
};

const ITEMS_MAX_LENGTH = 5;
