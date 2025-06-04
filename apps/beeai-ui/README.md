# BeeAI UI

## Custom navigation

By default, the header displays the agent's name and a detail button.

You can override this with a custom navigation.
To do so, add a `nav.json` file to the root of the project.
Example:

```json
[
  {
    "label": "Playground",
    "url": "/",
    "isActive": true
  },
  {
    "label": "Cookbooks",
    "url": "https://example.com/cookbooks",
    "isExternal": true
  },
  {
    "label": "Docs",
    "url": "https://example.com/docs",
    "isExternal": true
  },
  {
    "label": "Download Granite",
    "url": "https://example.com/download-granite",
    "isExternal": true,
    "position": "end"
  }
]
```

For more details, see the [schema](./src/modules/nav/schema.ts).

## ENV

See [`.env.example`](./.env.example).
