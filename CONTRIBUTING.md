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

### Running the platform

Starting up the platform using the CLI (`beeai platform start`, even `mise beeai-cli:run -- platform start`) will use **published images** by default. To use local images, you need to build them and import them into the platform.

Save a local `beeai-server` image using:

```sh
mise beeai-server:image:save
```

This will save the image to `~/.beeai/images/beeai-server.tar` tagged as `ghcr.io/i-am-bee/beeai-platform/beeai-server:local`.

Then, start the platform using:
```sh
mise beeai-cli:run -- platform start --import-images --set image.tag=local
```

### Running and debugging individual components

It's desirable to run and debug (i.e. in an IDE) individual components against the full stack (PostgreSQL, OpenTelemetry, Arize Phoenix, ...). For this, we include [Telepresence](https://telepresence.io/) which allows rewiring a Kubernetes container to your local machine.


```sh
mise run beeai-server:dev:start
```

This will do the following:
1. Create .env file if it doesn't exist yet (you can add your configuration here)
2. Stop default platform VM ("beeai") if it exists
3. Start a new VM named "beeai-local-dev" separate from the "beeai" VM used by default
4. Install telepresence into the cluster
   > Note that this will require **root access** on your machine, due to setting up a networking stack.
5. Replace beeai-platform in the cluster and forward any incoming traffic to localhost

After the command succeeds, you can:
- send requests as if your machine was running inside the cluster. For example: `curl http://<service-name>:<service-port>`.
- connect to postgresql using the default credentials `postgresql://beeai-user:password@postgresql:5432/beeai`
- now you can start your server from your IDE or using `mise run beeai-server:run` on port **18333**
- run beeai-cli using `mise beeai-cli:run -- <command>` or HTTP requests to localhost:8333 or localhost:18333
   - localhost:8333 is port-forwarded from the cluster, so any requests will pass through the cluster networking to the beeai-platform pod, which is replaced by telepresence and forwarded back to your local machine to port 18333
   - localhost:18333 is where your local platform should be running

To inspect cluster using `kubectl` or `k9s` and lima using `limactl`, activate the dev environment using:
```shell
# Activate dev environment
eval "$(mise run beeai-server:dev:shell)"
# Deactivate dev environment
deactivate
```

When you're done you can stop the development cluster and networking using
```shell
mise run beeai-server:dev:stop
```
Or delete the cluster entirely using
```shell
mise run beeai-server:dev:clean
```
<details>

<summary> Lower-level networking using telepresence directly</summary>

```shell
# Activate environment
eval "$(mise run beeai-server:dev:shell)"

# Start platform
mise beeai-cli:run -- platform start --vm-name=beeai-local-dev # optional --tag [tag] --import-images
mise x -- telepresence helm install
mise x -- telepresence connect --namespace beeai

# Receive traffic to a pod by replacing it in the cluster
mise x -- telepresence replace <pod-name>

# More information about how replace/intercept/ingress works can be found in the [Telepresence documentation](https://telepresence.io/docs/howtos/engage).
# Once done, quit Telepresence using:
```sh
mise x -- telepresence quit
```

</details>

#### Ollama
If you want to run this local setup against Ollama you must use a special option when setting up the LLM:
```
beeai env setup --use-true-localhost
```

### Running or creating migrations
The following commands can be used to create or run migrations in the dev environment above:

- Run migrations: `mise run beeai-server:migrations:run`
- Generate migrations: `mise run beeai-server:migrations:generate`
- Use Alembic command directly: `mise run beeai-server:migrations:alembic`

> Note: The dev setup will run the production image including its migrations before replacing it with your local 
> instance.

### Running individual components

To run BeeAI components in development mode (ensuring proper rebuilding), use the following commands.

#### Server
Build image and run the platform using:
```shell
mise run beeai-server:image:save
mise run beeai-cli:run -- platform start --import-images --set image.tag=local
```
Or use development setup described in [Running and debugging individual components](#Running and debugging individual components)

#### CLI

```sh
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

From the user's point of view, the server is part of the BeeAI CLI through `beeai platform start`, so usually after releasing `beeai-server`, you might want to bump the dependency version and release `beeai-cli` as well.

### Releasing `beeai-cli`

**⚠️ Ensure that the new version does not depend on unreleased changes of dependencies!**

Bump version in `apps/beeai-cli/pyproject.toml`. Commit the changes, push to main, and create and push a tag `beeai-cli-v<version>`, for example `beeai-cli-v0.0.1`. Check the GitHub Actions to see if everything went smoothly.

After releasing to PyPI, the next step is releasing to Homebrew: follow the [instructions in the Homebrew tap](https://github.com/i-am-bee/homebrew-beeai/blob/main/CONTRIBUTING.md).
