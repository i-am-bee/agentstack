# Agent Stack Helm Chart

The agent stack helm chart is packaged and uploaded to the container registry for every release.
You can install the chart using the following command:

```bash
helm install agentstack -f config.yaml oci://ghcr.io/i-am-bee/agentstack/chart/agentstack:<release-version>
```

Check out the [documentation](https://agentstack.beeai.dev/how-to/deployment-guide) for a detailed deployment guide.
