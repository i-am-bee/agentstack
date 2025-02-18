import { noop } from '@/utils/helpers';
import { createContext, ReactNode } from 'react';

export interface ModalProps {
  /** True if modal is open */
  isOpen: boolean;
  /** Called when modal requests to be closed, you should update isOpen prop there to false */
  onRequestClose: (force?: boolean) => void;
  /** Called when modal finished closing and unmounted from DOM */
  onAfterClose: () => void;
}

interface ModalRenderFn {
  (props: ModalProps): ReactNode;
}

export type OpenModalFn = (renderModal: ModalRenderFn) => () => void;

export interface ModalState {
  isOpen: boolean;
  renderModal: ModalRenderFn;
  onRequestClose: (force?: boolean) => void;
  onAfterClose: () => void;
}

export const ModalContext = createContext<OpenModalFn>(() => noop);
