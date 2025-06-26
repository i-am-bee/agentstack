/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

declare module '@carbon/layout' {
  // wrongly typed in @types/carbon__layout
  export const spacing: string[];

  export const baseFontSize: number;

  export const breakpoints: {
    lg: {
      columns: number;
      margin: string;
      width: string;
    };
    max: {
      columns: number;
      margin: string;
      width: string;
    };
    md: {
      columns: number;
      margin: string;
      width: string;
    };
    sm: {
      columns: number;
      margin: string;
      width: string;
    };
    xlg: {
      columns: number;
      margin: string;
      width: string;
    };
  };

  export const miniUnit: number;

  export function breakpoint(...args: unknown[]): string;

  export function breakpointDown(name: string): string;

  export function breakpointUp(name: string): string;

  export function em(px: number): string;

  export function miniUnits(count: number): string;

  export function px(value: number): string;

  export function rem(px: number): string;
}
