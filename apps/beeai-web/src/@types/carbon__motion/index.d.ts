/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

declare module '@carbon/motion' {
  export const fast01: string;
  export const fast02: string;
  export const moderate01: string;
  export const moderate02: string;
  export const slow01: string;
  export const slow02: string;
  // V11 Tokens
  export const durationFast01: string;
  export const durationFast02: string;
  export const durationModerate01: string;
  export const durationModerate02: string;
  export const durationSlow01: string;
  export const durationSlow02: string;

  type EasingMode = 'productive' | 'expressive';
  type EasingName = 'standard' | 'entrance' | 'exit';

  export const easings: Record<EasingName, Record<EasingMode, string>>;

  export function motion(name: EasingName, mode: EasingMode): string;
}
