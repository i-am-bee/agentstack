/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { z } from 'zod';

const navItemSchema = z.object({
  label: z.string(),
  url: z.union([z.string().url(), z.literal('/')]),
  isActive: z.boolean().optional(),
  isExternal: z.boolean().optional(),
  position: z.enum(['start', 'end']).optional(),
});

export const navSchema = z.array(navItemSchema);

export type NavItem = z.infer<typeof navItemSchema>;
