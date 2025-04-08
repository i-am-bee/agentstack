# Contributing

## Development setup

### Installation

This project uses [Mise-en-place](https://mise.jdx.dev/) as a manager of tool versions (`python`, `uv`, `nodejs`, `pnpm` etc.), as well as a task runner and environment manager. Mise will download all the needed tools automatically -- you don't need to install them yourself.

Clone this project, then run these setup steps:

```sh
brew install mise # more ways to install: https://mise.jdx.dev/installing-mise.html
mise trust
mise install
```

After setup, you can use:

* `mise run` to list tasks and select one interactively to run

* `mise <task-name>` to run a task

* `mise x -- <command>` to run a project tool -- for example `mise x -- uv add <package>`

If you want to run tools directly without the `mise x --` prefix, you need to activate a shell hook:

* Bash: `eval "$(mise activate bash)"` (add to `~/.bashrc` to make permanent)

* Zsh: `eval "$(mise activate zsh)"` (add to `~/.zshrc` to make permanent)

* Fish: `mise activate fish | source` (add to `~/.config/fish/config.fish` to make permanent)

* Other shells: [documentation](https://mise.jdx.dev/installing-mise.html#shells)

### Configuration

Edit `[env]` in `mise.local.toml` in the project root ([documentation](https://mise.jdx.dev/environments/)). Run `mise setup` if you don't see the file.

### Running

To run BeeAI components in development mode (ensuring proper rebuilding), use the following commands.

#### Server

```sh
# remove existing providers (due to breaking changes during rapid development)
rm -f ~/.beeai/providers.yaml

# API
mise beeai-server:run
# (keep it running, open another terminal for next steps)
```

#### CLI

```sh
# add official framework provider 
mise beeai-cli:run -- provider add file://agents/official/beeai-framework/beeai-provider.yaml

# tools
mise beeai-cli:run -- tool list
mise beeai-cli:run -- tool call fetch '{"url": "http://iambee.ai"}'

# agents
mise beeai-cli:run -- agent list
mise beeai-cli:run -- agent run website_summarizer "summarize iambee.ai"
```

#### UI

```sh
# run the UI development server:
mise beeai-ui:run

# UI is also available from beeai-server (in static mode):
mise beeai-server:run
```

---

## Releasing

This repository contains several projects which get released to NPM, PyPI, and/or Homebrew through GitHub Actions.

This is the general structure of dependency.

**⚠️ At the moment, we use strict versioning for dependencies, so most of the time you will need to bump the dependants as well!**

```mermaid
flowchart TD
    beeai-sdk --> acp
    agents --> beeai-sdk
    beeai-server --> beeai-sdk
    beeai-server --> beeai-ui
    beeai-cli --> beeai-server
```

### Releasing `acp-typescript-sdk` and `acp-python-sdk`

Update _both_ `packages/acp-typescript-sdk/package.json` and `packages/acp-python-sdk/pyproject.toml` to include the correct version. These two are released in sync. Commit the changes, push to main, and create and push a tag `acp-v<version>`, for example `acp-v0.0.1`. Check the GitHub Actions to see if everything went smoothly.

### Releasing `beeai-sdk`

`beeai-sdk` is actually two projects in a trenchcoat, one TypeScript and one Python. 

Update _both_ `packages/beeai-sdk/package.json` and `packages/beeai-sdk/pyproject.toml` to include the correct version. These two are released in sync. Commit the changes, push to main, and create and push a tag `beeai-sdk-v<version>`, for example `beeai-sdk-v0.0.1`. Check the GitHub Actions to see if everything went smoothly.

### Releasing agents

The platform automatically grabs the `provider-registry.yaml` file from the `main` branch of `https://github.com/i-am-bee/beeai`. In there, it finds URLs for agent provider manifests (`beeai-provider.yaml`), and in those manifests, it finds URLs to the agent provider implementations. At the moment, we use `agents-v*` tags, for example `agents-v0.0.1`.

In order to release a new version of an agent (or several agents at once), be sure to bumpt the version in the URL in **both** `beeai-provider.yaml` of the affected agents and the corresponding URLs in `provider-registry.yaml`.

To not accidentally bump the version in `provider-registry.yaml` before actually creating the tag, it's advised to first update `beeai-provider.yaml` file(s) and tag that commit, and update `provider-registry.yaml` in a later commit. Or use `git push --atomic main agents-v...`.

Wait a bit, or restart your local BeeAI service, and confirm using `beeai provider list` that the new versions have been loaded.

### Releasing `beeai-ui`

`beeai-ui` is statically included in `beeai-server`, so it can be considered a part of that project. It is not versioned separately. For any changes, `beeai-server` needs to be released.

### Releasing `beeai-server`

**⚠️ Ensure that the new version does not depend on unreleased changes of dependencies!**

Bump version in `apps/beeai-server/pyproject.toml`. Commit the changes, push to main, and create and push a tag `beeai-server-v<version>`, for example `beeai-server-v0.0.1`. Check the GitHub Actions to see if everything went smoothly.

From the user's point of view, the server is part of the BeeAI CLI through `beeai serve`, so usually after releasing `beeai-server`, you might want to bump the dependency version and release `beeai-cli` as well.

### Releasing `beeai-cli`

**⚠️ Ensure that the new version does not depend on unreleased changes of dependencies!**

Bump version in `apps/beeai-cli/pyproject.toml`. Commit the changes, push to main, and create and push a tag `beeai-cli-v<version>`, for example `beeai-cli-v0.0.1`. Check the GitHub Actions to see if everything went smoothly.

After releasing to PyPI, the next step is releasing to Homebrew: follow the [instructions in the Homebrew tap](https://github.com/i-am-bee/homebrew-beeai/blob/main/CONTRIBUTING.md).
