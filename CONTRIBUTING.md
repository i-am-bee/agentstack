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
mise agentstack:start --set auth.oidc.enabled=true --set auth.oidc.validate_audience=false --set auth.enabled=true
```

This does the following:

- Installs Istio in ambient mode.
- Creates a gateway and routes for `https://agentstack.localhost:8336/`.
- Installs the Kiali console.

**Why TLS is used:**  
OAuth tokens are returned to the browser only over HTTPS to avoid leakage over plain HTTP. Always access the UI via
`https://agentstack.localhost:8336/`.

**Istio details:**  
The default namespace is labeled `istio.io/dataplane-mode=ambient`. This ensures all intra-pod traffic is routed through
`ztunnel`, except the `agentstack` pod, which uses `hostNetwork` and is not compatible with the Istio mesh.

**Available endpoints:**

| Service        | HTTPS                                           | HTTP                                |
|----------------|-------------------------------------------------|-------------------------------------|
| Kiali Console  | –                                               | `http://localhost:20001`            |
| BeeAI UI       | `https://agentstack.localhost:8336`             | `http://localhost:8334`             |
| BeeAI API Docs | `https://agentstack.localhost:8336/api/v1/docs` | `http://localhost:8333/api/v1/docs` |

**OIDC configuration:**

- Update OIDC provider credentials and settings helm/values.yaml under:

```YAML
oidc:
  enabled: false
  default_new_user_role: "user"
  admin_emails:
    - admin@example.com
  nextauth_trust_host: true
  nextauth_secret: "<To generate a random string, you can use the Auth.js CLI: npx auth secret>"
  nextauth_url: "http://localhost:8336"
  validate_audience: false
  nextauth_providers: [
    {
      "name": "IBMiD-PKCE",
      "id": "ibmid-pkce",
      "type": "oidc",
      "class": "client",
      "client_id": "<ibm_security_vierfy_openid_connect_app_client_id>",
      "client_secret": "", # The client secret for a public client (PKCE) is an empty string.  This is the agentstack cli provider.
      "issuer": "<ibm_security_verify_issuer>" # e.g. "https://isg-verify1.verify.ibm.com/oauth2",
    },
    {
      "name": "IBM",
      "id": "sso-provisioned",
      "type": "oidc",
      "class": "ui", # this is the ui provider.
      "client_id": "<oidc_client_id>",
      "client_secret": "<oidc_client_secret>",
      "issuer": "<oidc_issuer>",
    }
  ]
```

- When debugging the ui component (See debugging individual components), copy the env.example as .env and update the
  following oidc specific values:

```JavaScript
OIDC_PROVIDERS = '[{"name": "w3id","id": "w3id","type": "oidc","class": "IBM","client_id": "<oidc_client_id>","client_secret": "<oidc_client_secret>","issuer": "<oidc_issuer>"}]'
NEXTAUTH_SECRET = "<To generate a random string, you can use the Auth.js CLI: npx auth secret>"
NEXTAUTH_URL = "http://localhost:3000"
OIDC_ENABLED = true
```

Optionally add:

```JavaScript
NEXTAUTH_DEBUG = "true"
```

**To deploy the helm chart to OpenShift:**

- Update values.yaml so that auth.enabled and auth.oidc.enabled are true. e.g.:

```yaml
auth:
  enabled: true
  ...
  odic:
    enabled: true
```

- Update values.yaml so that the `nextauth_url` and the `nextauth_redirect_proxy_url` values reflect the URL for the
  route created for the `agentstack-ui-svc`.
- Ensure that the oidc.nextauth_providers array entries in values.yaml have valid/appropriate values

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

- send requests as if your machine was running inside the cluster. For example:
  `curl http://<service-name>:<service-port>`.
- connect to postgresql using the default credentials `postgresql://agentstack-user:password@postgresql:5432/agentstack`
- now you can start your server from your IDE or using `mise run agentstack-server:run` on port **18333**
- run agentstack-cli using `mise agentstack-cli:run -- <command>` or HTTP requests to localhost:8333 or localhost:18333
    - localhost:8333 is port-forwarded from the cluster, so any requests will pass through the cluster networking to the
      agentstack pod, which is replaced by telepresence and forwarded back to your local machine to port 18333
    - localhost:18333 is where your local platform should be running

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

We use a separate VM for local development of e2e and integration tests, the setup is almost identical,
but you need to change kubeconfig location in your .env:

```shell
# Use for developing e2e and integration tests locally
K8S_KUBECONFIG=~/.agentstack/lima/agentstack-local-test/copied-from-guest/kubeconfig.yaml
```

and then run `agentstack-server:dev:test:start`

> TIP: Similarly to dev environment you can use `mise run agentstack-server:dev:test:reconnect`

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

# More information about how replace/intercept/ingress works can be found in the [Telepresence documentation](https://telepresence.io/docs/howtos/engage).
# Once done, quit Telepresence using:
```sh
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

- Run migrations: `mise run agentstack-server:migrations:run`
- Generate migrations: `mise run agentstack-server:migrations:generate`
- Use Alembic command directly: `mise run agentstack-server:migrations:alembic`

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
mise agentstack-cli:run -- agent run website_summarizer "summarize iambee.ai"
```

#### UI

```sh
# run the UI development server:
mise agentstack-ui:run

# UI is also available from agentstack-server (in static mode):
mise agentstack-server:run
```

## Releasing

> ⚠️ **IMPORTANT**   
> Always create pre-release before the actual public release and check that the upgrade and installation work.

Use the release script:

```shell
mise run release
```

