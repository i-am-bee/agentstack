# Contributing

## Development setup

### Installation

This project uses [Mise-en-place](https://mise.jdx.dev/) as a manager of tool versions (`python`, `uv`, `nodejs`, `pnpm`
etc.), as well as a task runner and environment manager. Mise will download all the needed tools automatically -- you
don't need to install them yourself.

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

Edit `[env]` in `mise.local.toml` in the project root ([documentation](https://mise.jdx.dev/environments/)). Run
`mise setup` if you don't see the file.

### Running the platform from source

Starting up the platform using the CLI (`agentstack platform start`, even `mise agentstack-cli:run -- platform start`)
will use
**published images** by default. To use local images, you need to build them and import them into the platform.

Instead, use:

```shell
mise agentstack:start
```

This will build the images (`agentstack-server` and `agentstack-ui`) and import them to the cluster. You can add other
CLI arguments as you normally would when using `agentstack` CLI, for example:

```shell
mise agentstack:start --set docling.enabled=true --set oidc.enabled=true 
```

To stop or delete the platform use

```shell
mise agentstack:stop
mise agentstack:delete
```

For debugging and direct access to kubernetes, setup `KUBECONFIG` and other environment variables using:

```shell
# Activate environment
eval "$(mise run agentstack:shell)"

# Deactivate environment
deactivate
```

### OAuth/OIDC authentication for local testing

By default, authentication and authorization are disabled.

Starting the platform with OIDC enabled:

```bash
mise agentstack:start --set auth.enabled=true
```

This will setup keycloak (with no platform users out of the box).

You can add users at <http://localhost:8336>, by loggin in with the admin user (admin:admin in dev)
and going to "Manage realms" -> "Users".

You can promote users by assigning `agentstack-admin` or `agentstack-developer` roles to them. Make sure to add a
password in the "Credentials" tab and set their email to verified.

You can also automate this by creating a file `config.yaml`:

```yaml
auth:
  enabled: true
keycloak:
  auth:
    seedAgentstackUsers:
      - username: admin
        password: admin
        firstName: Admin
        lastName: User
        email: admin@beeai.dev
        roles: ["agentstack-admin"]
        enabled: true
```

Then run `mise run agentstack:start -f config.yaml`

**Available endpoints:**

| Service              | HTTP                                |
|----------------------|-------------------------------------|
| Keycloak             | `http://localhost:8336`             |
| Agent Stack UI       | `http://localhost:8334`             |
| Agent Stack API Docs | `http://localhost:8333/api/v1/docs` |

**OIDC configuration:**

* UI: follow `template.env` in `apps/agentstack-ui` directory (copy to `apps/agentstack-ui/.env`).
* Server: follow `template.env` in `apps/agentstack-server` directory (copy to `apps/agentstack-server/.env`).

### Running and debugging individual components

It's desirable to run and debug (i.e. in an IDE) individual components against the full stack (PostgreSQL,
OpenTelemetry, Arize Phoenix, ...). For this, we include [Telepresence](https://telepresence.io/) which allows rewiring
a Kubernetes container to your local machine. (Note that `sshfs` is not needed, since we don't use it in this setup.)

```sh
mise run agentstack-server:dev:start
```

This will do the following:

1. Create .env file if it doesn't exist yet (you can add your configuration here)
2. Stop default platform VM ("agentstack") if it exists
3. Start a new VM named "agentstack-local-dev" separate from the "agentstack" VM used by default
4. Install telepresence into the cluster
   > Note that this will require **root access** on your machine, due to setting up a networking stack.
5. Replace agentstack in the cluster and forward any incoming traffic to localhost

After the command succeeds, you can:

* send requests as if your machine was running inside the cluster. For example:
  `curl http://<service-name>:<service-port>`.
* connect to postgresql using the default credentials `postgresql://agentstack-user:password@postgresql:5432/agentstack`
* now you can start your server from your IDE or using `mise run agentstack-server:run` on port **18333**
* run agentstack-cli using `mise agentstack-cli:run -- <command>` or HTTP requests to localhost:8333 or localhost:18333
  * localhost:8333 is port-forwarded from the cluster, so any requests will pass through the cluster networking to the
      agentstack pod, which is replaced by telepresence and forwarded back to your local machine to port 18333
  * localhost:18333 is where your local platform should be running

To inspect cluster using `kubectl` or `k9s` and lima using `limactl`, activate the dev environment using:

```shell
# Activate dev environment
eval "$(mise run agentstack-server:dev:shell)"

# Deactivate dev environment
deactivate
```

When you're done you can stop the development cluster and networking using

```shell
mise run agentstack-server:dev:stop
```

Or delete the cluster entirely using

```shell
mise run agentstack-server:dev:delete
```

> TIP: If you run into connection issues after sleep or longer period of inactivity
> try `mise run agentstack-server:dev:reconnect` first. You may not need to clean and restart
> the entire VM

#### Developing tests

To run and develop agentstack-server tests locally use `mise run agentstack-server:dev:start` from above.

> Note:
>
> * Some tests require additional settings (e.g. enabling authentication), see section for tests in `template.env` for more details.
> * Tests will drop your database - you may need to add agents again or reconfigure model

Locally, the default model for tests is configured in `apps/agentstack-server/tests/conftest.py` (`llama3.1:8b` from ollama).
Make sure to have this model running locally.

<details>
<summary> Lower-level networking using telepresence directly</summary>

```shell
# Activate environment
eval "$(mise run agentstack-server:dev:shell)"

# Start platform
mise agentstack-cli:run -- platform start --vm-name=agentstack-local-dev # optional --tag [tag] --import-images
mise x -- telepresence helm install
mise x -- telepresence connect

# Receive traffic to a pod by replacing it in the cluster
mise x -- telepresence replace <pod-name>

# More information about how replace/intercept/ingress works: https://telepresence.io/docs/howtos/engage

# Once done, quit Telepresence using:
mise x -- telepresence quit
```

</details>

#### Ollama

If you want to run this local setup against Ollama you must use a special option when setting up the LLM:

```
agentstack model setup --use-true-localhost
```

### Working with migrations

The following commands can be used to create or run migrations in the dev environment above:

* Run migrations: `mise run agentstack-server:migrations:run`
* Generate migrations: `mise run agentstack-server:migrations:generate`
* Use Alembic command directly: `mise run agentstack-server:migrations:alembic`

> NOTE: The dev setup will run the locally built image including its migrations before replacing it with your local
> instance. If new migrations you just implemented are not working, the dev setup will not start properly and you need
> to fix migrations first. You can activate the shell using `eval "$(mise run agentstack-server:dev:shell)"` and use
> your favorite kubernetes IDE (e.g., k9s or kubectl) to see the migration logs.

### Running individual components

To run Agent Stack components in development mode (ensuring proper rebuilding), use the following commands.

#### Server

Build and run server using setup described in [Running the platform from source](#running-the-platform-from-source)
Or use development setup described
in [Running and debugging individual components](#running-and-debugging-individual-components)

#### CLI

```sh
mise agentstack-cli:run -- agent list
mise agentstack-cli:run -- agent run website_summarizer "summarize beeai.dev"
```

#### UI

```sh
# run the UI development server:
mise agentstack-ui:run

# UI is also available from agentstack-server (in static mode):
mise agentstack-server:run
```

## Releasing

Agent Stack is using `main` branch for next version development (integration branch) and `release-v*` branches for stable releases.

The release process consists of three steps:

### Step 1: Cut the release

Ensure that the currently set version in `main` branch is the desired release version. If not, first run `mise run release:set-version <new-version>`.

Run the `release:new` task from the `main` branch:

```shell
mise run release:new
```

This will prepare a new branch `release-vX.Y` (with the version number from `main`), and bump up the version in `main` to the next patch version (e.g., `1.2.3` -> `1.2.4`).

### Step 2: QA & Polish the release on release branch

You can then iteratively polish the release in `release-v*` branch. Do not forget to apply relevant fixes to both the release branch and `main`, e.g. by `git cherrypick`.

To publish a release candidate from the release branch, run `mise run release:publish-rc`. This will publish `X.Y.Z-rcN` version, where `N` is incremented on each RC publish.

Creating new RC will trigger GH action to deploy pre-release version of the package for testing.

### Step 3: Publish

Once the RC makes the QA rounds, publish the final release from the release branch:

```shell
mise run release:publish-stable
```

In addition to publishing the stable version, this action also ensures that the docs in `main` branch are updated to reflect the new version by moving the `docs/development` folder from the release branch to `docs/stable` on `main`.

## Documentation

There are two documentation folders: `docs/stable` and `docs/development`. Due to the nature of Mintlify, docs are deployed from the `main` branch, so we keep `docs/stable` frozen to correspond to the latest stable release. **Only make manual changes in `docs/stable` in order to fix issues with the docs, feature PRs should only edit `docs/development`.**

All PRs **must** either include corresponding documentation in `docs/development`, or include `[x] No Docs Needed` in the PR description. This is checked by GitHub Actions.

Special care needs to be taken with the `docs/development/reference/cli-reference.mdx` file, which is automatically generated. Use `mise run agentstack-cli:docs` to regenerate this file when modifying the CLI interface.

Try to follow this structure:

- **Elevator pitch:** What value this feature brings to the user.
- **Pre-requisites:** Extra dependencies required on top of Agent Stack -- non-default agents, Docker runtime, 3rd party libraries, environment variables like API keys, etc. (Note that `uv` is part of the Agent Stack install.)
- **Step-by-step instructions**
- **Troubleshooting:** Common errors and solutions.

Make sure to preview docs locally using: `mise docs:run`. This runs a development server which refreshes as you make changes to the `.mdx` files.
