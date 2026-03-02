# Step 6 – Forms (Single-Turn Structured Input)

If the original agent accepts **named parameters** (not just free text), map them to an `initial_form` using the Forms extension.

1. Define a `FormRender` with appropriate field types (`TextField`, `DateField`, `CheckboxField`, etc.). Always use `fields=[...]` (not `items=[...]`) and `label="..."` (not `title="..."`).
2. Create a Pydantic `BaseModel` matching the form fields
3. Add `form: Annotated[FormServiceExtensionServer, FormServiceExtensionSpec.demand(initial_form=form_render)]` as an agent parameter
4. Parse input via `form.parse_initial_form(model=MyParams)`

Only use forms when the agent has clearly defined, structured parameters. For free-text agents, the plain message input is sufficient.

## Mid-Conversation Input

- Single free-form question, use A2A `input-required` event.
- Structured multi-field input, use dynamic form request extension (`FormRequestExtensionServer` / `FormRequestExtensionSpec`).

See the [form agent example](https://github.com/i-am-bee/agentstack/blob/main/agents/form/src/form/agent.py) on GitHub for a complete implementation.
