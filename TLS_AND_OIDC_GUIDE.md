# How to set up internal TLS with istio ambient mode

- Copy the apps/beeai-cli/.env.template as .env
- To turn on oauth on platform startup set `BEEAI__OIDC_ENABLED=True` in the .env file.
- Add an entry to /etc/hosts on your local system:
```
# Added by BEEAI-PLATFORM
127.0.0.1        beeai-platform.api.testing
```

- Update OAuth credentials in helm/values.yaml under:

```YAML
oidc:
  enabled: true
  discovery_url: <your_oidc_discovery_endpoint_here>
  client_id: <your_client_id_here>
  client_secret: <your_oidc_client_secret>
  issuer: <your_issuer>
  jwks_url: <your_jwks_endpoint_here>
  nextauth_trust_host: true
  nextauth_url: "https://beeai-platform.api.testing:8336"
  nextauth_redirect_proxy_url: "https://beeai-platform.api.testing:8336"
  nextauth_secret: "<To generate a random string, you can use the Auth.js CLI: npx auth secret>
```

When the environment variable, "BEEAI__OIDC_ENABLED" is set to true, the platform will install istio in ambient mode, create a gateway & routes for `https://beeai-platform.api.testing:8336/`.  The intent being that tokens returned by OAuth routes are receieved in the browser over HTTPS rather than plain text HTTP to prevent unauthorized use of tokens.   It is strongly recommended that you access the UI via the TLS connection `https://beeai-platform.api.testing:8336/`, and configure your OIDC provider to use `https://beeai-platform.api.testing:8336/` as one of the allowed redirect urls.  In practice when deploying the beeai images to a cloud cluster, change the nextauth_url, and nextauth_redirect_proxy_url values accordingly.   Some OIDC providers only allow valid top level domain names in the redirect urls.

The default namespace is labeled istio.io/dataplane-mode=ambient so all intra pod trafic is via ztunnel with the exception of the beeai-platform pod due to it's use of the hostNetwork (istio can not bring a hostNetwork enabled pod into the mesh).

The Kiali console is installed when BEEAI_OIDC_ENABLED is set to True.  The port can be found by shelling into the VM and running the following kuberneties command:
```bash
limactl shell --workdir / beeai-platform
habeck@lima-beeai-platform:/$ kubectl -n istio-system get svc | grep "kiali-external" | awk '{print $5}' | cut -d ':' -f2 | cut -d '/' -f1 
30431
```
Using the output from the above command navigate to `http://localhost:30431/kiali/console`

