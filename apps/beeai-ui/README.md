# BeeAI UI

## ENV

See [`.env.example`](./.env.example).

## Custom navigation

By default:

- The **header** displays the **current agent's name** and a detail button.
- The **sidebar** displays the list of **agents**.

You can override this by providing a custom navigation.
To do so, set `NEXT_PUBLIC_NAV_ITEMS` as a JSON-stringified value.

Example (before stringification):

```json
[
  {
    "label": "Playground",
    "url": "/",
    "activePathnames": ["/", "/agents"]
  },
  {
    "label": "Cookbooks",
    "url": "/docs/cookbooks",
    "isExternal": true,
    "target": "_self"
  },
  {
    "label": "Docs",
    "url": "/docs",
    "isExternal": true,
    "target": "_self"
  },
  {
    "label": "Download Granite",
    "url": "https://huggingface.co/ibm-granite/granite-3.3-8b-instruct",
    "isExternal": true,
    "position": "end"
  }
]
```

For more details, see the [schema](./src/modules/nav/schema.ts).
