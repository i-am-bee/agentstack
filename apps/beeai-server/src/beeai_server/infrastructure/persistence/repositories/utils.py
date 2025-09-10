# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
from enum import StrEnum
from typing import NamedTuple
from uuid import UUID

from sqlalchemy import Column, Enum, Row, Select, func, select
from sqlalchemy.ext.asyncio import AsyncConnection


def sql_enum(enum: type[StrEnum], **kwargs) -> Enum:
    return Enum(enum, values_callable=lambda x: [e.value for e in x], **kwargs)


class CursorPaginationResult(NamedTuple):
    items: Sequence[Row]
    total_count: int
    has_more: bool


async def cursor_paginate(
    connection: AsyncConnection,
    query: Select,
    order_column: Column,
    id_column: Column,
    limit: int,
    after_cursor: UUID | None = None,
    order: str = "desc",
) -> CursorPaginationResult:
    """
    Implements cursor-based pagination for non-unique columns.

    For non-unique columns, we use a composite cursor approach:
    - Primary cursor: the order column value
    - Secondary cursor: the ID for tie-breaking

    This ensures stable, consistent pagination even when multiple rows
    have the same value in the order column.
    """

    # Apply cursor filtering if after_cursor is provided
    if after_cursor:
        # Get the cursor row's order column value and ID
        cursor_query = select(order_column, id_column).where(id_column == after_cursor)
        cursor_result = await connection.execute(cursor_query)
        cursor_row = cursor_result.fetchone()

        if cursor_row:
            cursor_order_value = cursor_row[0]  # order column value
            cursor_id = cursor_row[1]  # ID value

            if order == "desc":
                # For descending: include rows where order_col < cursor_value
                # OR (order_col = cursor_value AND id < cursor_id)
                query = query.where(
                    (order_column < cursor_order_value)
                    | ((order_column == cursor_order_value) & (id_column < cursor_id))
                )
            else:
                # For ascending: include rows where order_col > cursor_value
                # OR (order_col = cursor_value AND id > cursor_id)
                query = query.where(
                    (order_column > cursor_order_value)
                    | ((order_column == cursor_order_value) & (id_column > cursor_id))
                )

    # Apply ordering with tie-breaking by ID
    if order == "desc":
        query = query.order_by(order_column.desc(), id_column.desc())
    else:
        query = query.order_by(order_column.asc(), id_column.asc())

    # Fetch one more than limit to determine if there are more results
    count_query_base = query.order_by(None)
    query = query.limit(limit + 1)

    # Execute query
    result = await connection.execute(query)
    rows = result.fetchall()

    has_more = len(rows) > limit

    # Reset the limit and order for count query
    count_query = select(func.count()).select_from(count_query_base.subquery())

    count_result = await connection.execute(count_query)
    total_count = count_result.scalar() or 0

    return CursorPaginationResult(items=rows[:limit], total_count=total_count, has_more=has_more)
