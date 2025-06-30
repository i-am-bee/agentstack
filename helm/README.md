# Install

Create a value file with the minimum configuration

`config.yaml`:

```yaml
# If you want to include agents from the default catalog (change release/tag accordingly):
externalRegistries:
  public_github: "https://github.com/i-am-bee/beeai-platform@release-v0.2.0#path=agent-registry.yaml"

# Your custom agents as docker images
providers:
  # e.g.
  # - location: ghcr.io/i-am-bee/beeai-platform-agent-starter/my-agent:latest
  - location: <docker-image-id>

# Generate the encryption key:
#  - using UV (https://docs.astral.sh/uv/getting-started/installation/)
#   $ uv run --with cryptography python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
#  - using python3 directly
#   $ python3 -m pip install cryptography # (or use your preferred way to install the cryptography package)
#   $ python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
encryptionKey: "encryption-key-from-command"

features:
  uiNavigation: true

# this requires passing an admin password to certain endpoints, you can disable auth for insecure deployments
auth:
  enabled: true
  admin_password: "my-secret-password"
```

Then install the chart using

```shell
helm install -f config.yaml beeai oci://ghcr.io/i-am-bee/beeai-platform/beeai-platform-chart/beeai-platform:0.2.9
```

After the beeai-platform becomes ready, it's necessary to configure the LLM provider. We will use the `admin-password`
you created earlier and your preferred LLM credentials, for example:

## Setup LLM

```shell
beeai platform exec -- kubectl run curlpod --image=curlimages/curl -it --rm --restart=Never -- curl -X PUT \
  beeai-platform-svc:8333/api/v1/variables \
  -u beeai-admin:my-secret-password \
  -H "Content-Type: application/json" \
  -d '{
    "env": {
        "LLM_API_BASE": "https://api.openai.com/v1",
        "LLM_API_KEY": "sk-...",
        "LLM_MODEL": "gpt-4o"
    }
  }'
```

## Use the platform

Test that the platform is working:

# port-forward in a separate terminal

```shell
kubectl port-forward svc/beeai-platform-svc 8333:8333 &
```

```
beeai list
beeai run chat hi
```

# Upgrading

To upgrade to a newer version of the beeai platform, use

```
helm upgrade --install -f config.yaml beeai oci://ghcr.io/i-am-bee/beeai-platform/beeai-platform-chart/beeai-platform:<newer-version>
```

## External Services

### External S3 support

You may want to have beeai platform connect to an external storage streaming rather than installing seaweedfs inside
your cluster. To achieve this, the chart allows you to specify credentials for an external storage streaming with the
`externalS3`. You should also disable the seaweedfs installation with the `seaweedfs.enabled`
option. Here is an example:

```console
seaweedfs.enabled=false
externalS3.host=myexternalhost
exterernalS3.accessKeyID=accesskey
externalS3.accessKeySecret=secret
```