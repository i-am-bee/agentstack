/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import './styles/style.scss';

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Needs to be after style.scss
import { App } from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
