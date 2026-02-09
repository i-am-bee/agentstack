/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  ActionProvider,
  ComponentRegistry,
  DataProvider,
  Renderer,
  SetData,
  useActions,
  VisibilityProvider,
} from '@json-render/react';
import { defineCatalog, Spec } from '@json-render/core';
import { schema } from '@json-render/react';
import { Button, InlineLoading } from '@carbon/react';
import { z } from 'zod';
import { ReactNode, useMemo, useRef } from 'react';

export const catalog = defineCatalog(schema, {
  components: {
    Button: {
      props: z.object({
        label: z.string(),
        action: z.string(),
        kind: z.enum(['primary', 'secondary', 'tertiary', 'ghost', 'danger']).optional(),
        size: z.enum(['sm', 'md', 'lg']).optional(),
      }),
      description: 'Clickable button (Carbon Button)',
    },
    VerticalContainer: {
      props: z.object({
        gap: z.number().optional(),
      }),
      hasChildren: true,
      description: 'Container that stacks children vertically',
    },
    Paragraph: {
      props: z.object({
        text: z.string(),
      }),
      description: 'Text paragraph',
    },
    HorizontalContainer: {
      props: z.object({
        gap: z.number().optional(),
      }),
      hasChildren: true,
      description: 'Container that stacks children horizontally',
    },
  },
  actions: {
    button_click: { params: z.object({ button_id: z.string() }), description: 'Submits the button' },
  },
});

const Btn = ({ props, loading }: { props: Record<string, unknown>; loading?: boolean }) => {
  const action = useActions();
  const elementKey = props.elementKey as string;
  const label = props.label as string;
  const kind = (props.kind as string | undefined) ?? 'primary';
  const size = (props.size as string | undefined) ?? 'md';

  return (
    <Button
      kind={kind as 'primary'}
      size={size as 'md'}
      disabled={loading}
      onClick={() => {
        action.handlers.button_click({ button_id: elementKey });
      }}
    >
      {loading ? <InlineLoading /> : label}
    </Button>
  );
};

const components = {
  Button: Btn,
  VerticalContainer: ({ props, children }: { props: Record<string, unknown>; children?: ReactNode }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: (props.gap as number | undefined) ?? 8 }}>
      {children}
    </div>
  ),
  Paragraph: ({ props }: { props: Record<string, unknown> }) => <p>{props.text as string}</p>,
  HorizontalContainer: ({ props, children }: { props: Record<string, unknown>; children?: ReactNode }) => (
    <div style={{ display: 'flex', flexDirection: 'row', gap: (props.gap as number | undefined) ?? 8 }}>{children}</div>
  ),
};

interface RendererProps {
  spec: Spec | null;
  data?: Record<string, unknown>;
  setData?: SetData;
  onDataChange?: (path: string, value: unknown) => void;
  loading?: boolean;
  onButtonClick?: (elementKey: string) => void;
}

// Build registry - uses refs to avoid recreating on data changes
function buildRegistry(
  dataRef: React.RefObject<Record<string, unknown>>,
  setDataRef: React.RefObject<SetData | undefined>,
  loading?: boolean,
): ComponentRegistry {
  const registry: ComponentRegistry = {};

  for (const [name, componentFn] of Object.entries(components)) {
    registry[name] = (renderProps: { element: { props: Record<string, unknown>; key: string }; children?: ReactNode }) => {
      return componentFn({
        props: { ...renderProps.element.props, elementKey: renderProps.element.key } as never,
        children: renderProps.children,
        loading,
      });
    };
  }

  return registry;
}

const fallbackRegistry = (renderProps: { element: { type: string } }) => (
  <div>Fallback: {renderProps.element.type}</div>
);

export function GenerativeInterfaceRenderer({
  spec,
  data = {},
  setData,
  onDataChange,
  loading,
  onButtonClick,
}: RendererProps) {
  const dataRef = useRef(data);
  const setDataRef = useRef(setData);
  dataRef.current = data;
  setDataRef.current = setData;

  const registry = useMemo(() => buildRegistry(dataRef, setDataRef, loading), [loading]);

  if (!spec) return null;

  return (
    <DataProvider initialData={data} onDataChange={onDataChange}>
      <VisibilityProvider>
        <ActionProvider
          handlers={{
            button_click: ({ button_id }: { button_id: string }) => {
              onButtonClick?.(button_id);
            },
          }}
        >
          <Renderer spec={spec} registry={registry} fallback={fallbackRegistry} loading={loading} />
        </ActionProvider>
      </VisibilityProvider>
    </DataProvider>
  );
}
