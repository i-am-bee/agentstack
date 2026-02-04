/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any */

declare module 'typewriter-effect' {
  import type { Component } from 'react';

  export interface TypewriterOptions {
    options: {
      strings?: string | string[];
      autoStart?: boolean;
      loop?: boolean;
      delay?: number | 'natural';
      deleteSpeed?: number | 'natural';
      cursor?: string;
      wrapperClassName?: string;
      cursorClassName?: string;
    };
    onInit?: (typewriter: any) => void;
    onCreateTextNode?: (character: string, node: Text) => Text;
    onRemoveNode?: (obj: { node: Text; character: string }) => void;
  }

  export default class Typewriter extends Component<TypewriterOptions> {
    typeString(string: string): this;
    pauseFor(ms: number): this;
    deleteAll(speed?: number): this;
    deleteChars(amount: number): this;
    callFunction(cb: (state: any) => void, thisArg?: any): this;
    changeDelay(delay: number): this;
    changeDeleteSpeed(speed: number): this;
    start(): this;
    stop(): this;
  }
}
