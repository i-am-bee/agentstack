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

## Turn Detection Guard (for multi-turn agents that also use initial forms)

Do **not** determine first-turn vs follow-up by checking whether `form.parse_initial_form(...)` returned an object. The initial form is available beyond the first interaction.

Use this decision order instead:

1. Load prior session state from `context.load_history()`.
2. If no stored state exists, treat the request as the initial turn and parse/require form fields.
3. If stored state exists, treat the request as a follow-up turn and ignore form truthiness for routing.
