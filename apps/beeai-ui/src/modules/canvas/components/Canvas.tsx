/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useRef } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import classes from './Canvas.module.scss';
import { Toolbar } from './Toolbar';

export function Canvas() {
  const contentRef = useRef(null);

  return (
    <div className={classes.root}>
      <header className={classes.header}>
        <h2 className={classes.heading}>Cozy Winter Dinner Party Menu</h2>

        <div className={classes.actions}>
          <CopyButton contentRef={contentRef} />
        </div>
      </header>

      <div className={classes.body} ref={contentRef}>
        <Toolbar isVisible />

        <MarkdownContent className={classes.content}>{`
## Appetizer
- **Baked Brie with Roasted Garlic & Thyme** – Served with toasted baguette slices and a drizzle of honey.
- **Creamy Roasted Cauliflower Soup** – Smooth, velvety, and finished with crispy shallots and a touch of truffle oil.

## Main Course
- **Braised Short Ribs with Red Wine & Rosemary** – Slow-cooked until fall-apart tender, served over garlic mashed potatoes.
- **Roasted Root Vegetables with Citrus Glaze** – A mix of carrots, parsnips, and beets with a honey-orange glaze.

## Side Dish
- **Sautéed Brussels Sprouts with Pancetta & Balsamic Reduction** – A balance of crispy, smoky, and tangy flavors.

## Dessert
- **Blood Orange & Olive Oil Cake** – Moist, citrusy, and served with whipped mascarpone.
- **Dark Chocolate Pots de Crème** – Rich and velvety, topped with a sprinkle of sea salt.

## Drinks
- **Mulled Wine** – Red wine infused with warm spices and citrus.
- **Hazelnut Hot Chocolate** – Creamy, nutty, and perfect for a cozy evening.
        `}</MarkdownContent>
      </div>
    </div>
  );
}
