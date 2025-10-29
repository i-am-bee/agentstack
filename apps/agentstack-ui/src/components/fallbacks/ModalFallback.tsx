/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ModalBody, ModalFooter, ModalHeader } from '@carbon/react';
import type { FallbackProps } from 'react-error-boundary';

import { getErrorMessage } from '#api/utils.ts';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import { Modal } from '../Modal/Modal';

interface Props extends FallbackProps, ModalProps {}

export function FallbackModal({ error, resetErrorBoundary, ...props }: Props) {
  const errorMessage = getErrorMessage(error) ?? `${error}`;

  return (
    <Modal {...props} size="xs">
      <ModalHeader title="Error" />
      <ModalBody>
        <p>{errorMessage}</p>
      </ModalBody>
      <ModalFooter secondaryButtonText="Close" primaryButtonText="Try again" onRequestSubmit={resetErrorBoundary}>
        {/* Hack to satisfy bug in Carbon - children is required in ModalFooterProps by mistake */}
        {''}
      </ModalFooter>
    </Modal>
  );
}
