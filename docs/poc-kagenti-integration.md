# PoC: Kagenti Integration into Agentstack

## Status: Draft / Brainstorming

---

## 1. Executive Summary

This document outlines the plan to refactor the agentstack platform so that agent scaling, deployment, and discovery are handled by **kagenti** instead of our custom Kubernetes provider management. The goal is a lightweight local developer experience with optional enterprise features (Istio, SPIRE, Shipwright).

### What We Gain
- Standard A2A agent lifecycle management (deploy, discover, scale)
- Realtime agent card discovery (no more storing cards in DB or Docker labels)
- Zero-trust identity via SPIRE/SPIFFE (optional)
- Service mesh observability via Istio Ambient (optional)
- Shipwright-based builds replacing our Kaniko pipeline (optional)
- Team namespace isolation

### What We Drop
- `KubernetesProviderDeploymentManager` (custom kr8s-based deployment logic)
- `KubernetesProviderBuildManager` (Kaniko build jobs with Docker label baking)
- Agent card storage in database / Docker image labels
- Scale-to-zero logic (kagenti handles agent lifecycle)
- The concept of "managed" vs "unmanaged" providers (all agents become kagenti-managed)

---

## 2. Architecture Comparison

### Current Agentstack
```
Lima VM (MicroShift)
└── agentstack namespace
    ├── agentstack-server (FastAPI)
    │   ├── KubernetesProviderDeploymentManager (kr8s)
    │   ├── KubernetesProviderBuildManager (Kaniko)
    │   ├── A2A Proxy Service
    │   └── Provider Registry sync
    ├── Keycloak (StatefulSet, port 8336)
    ├── PostgreSQL
    ├── Redis
    ├── SeaweedFS
    ├── Phoenix (observability)
    └── agentstack-provider-{id}-svc (per-agent deployments)
```

### Target: Agentstack + Kagenti
```
Lima VM (MicroShift)
├── agentstack namespace
│   ├── agentstack-server (FastAPI, slimmed down)
│   │   ├── A2A Proxy → delegates to kagenti agent services
│   │   └── Provider Registry → reads from kagenti API / agent cards
│   ├── PostgreSQL
│   ├── Redis
│   └── SeaweedFS
├── keycloak namespace (shared)
│   └── Keycloak (StatefulSet)
├── kagenti-system namespace
│   ├── kagenti-operator
│   ├── kagenti-webhook
│   ├── kagenti-ui (backend + frontend) [optional]
│   └── MCP Gateway
├── team1, team2, ... (agent namespaces)
│   └── agent Deployments + Services
├── istio-system (optional)
├── zero-trust-workload-identity-manager (optional)
└── cr-system (container registry, optional)
```

---

## 3. Key Integration Decisions

### 3.1 Installing Kagenti into MicroShift

**Problem:** Kagenti's installer uses Ansible + Kind. Our stack uses Lima + MicroShift. These are incompatible.

**Options:**

#### Option A: Helm-only installation (DECIDED)
Strip kagenti down to just its two Helm charts (`kagenti` and `kagenti-deps`) and install them directly into MicroShift via `helm install`. Skip the Ansible playbook entirely.

**Pros:**
- Clean, declarative, reproducible
- Integrates with our existing Helm-based deployment
- No Ansible dependency
- Can selectively enable/disable components via values

**Cons:**
- Some Ansible tasks do pre/post-processing (OAuth secret creation, DNS setup, image preloading)
- Need to replicate essential Ansible logic in our Lima provisioning or Helm hooks

**What Ansible does that we'd need to replicate:**
1. Cluster creation → already handled by Lima/MicroShift
2. DNS setup → already handled by Lima networking
3. OAuth secret creation → can be Helm hooks or init containers
4. Image preloading → can be pre-pull in Lima config
5. Shipwright ClusterBuildStrategy → can be a Helm template or post-install hook

#### Option B: Adapt Ansible to target MicroShift
Modify kagenti's Ansible playbook to target an existing MicroShift cluster instead of creating a Kind cluster.

**Pros:**
- Reuses kagenti's tested installation flow
- Less risk of missing setup steps

**Cons:**
- Ansible dependency for our stack
- Tight coupling to kagenti's playbook (maintenance burden)
- OpenShift-specific tasks may conflict with MicroShift

#### Option C: Umbrella Helm chart
Create a single umbrella chart that includes agentstack + kagenti + kagenti-deps as subcharts.

**Pros:**
- Single `helm install` for everything
- Shared values file for cross-component config
- Clean dependency management

**Cons:**
- Chart dependency version management
- Large chart, slower iteration
- Kagenti charts may need modifications to work as subcharts

**Decision:** **Option A** for the PoC. Evolve toward **Option C** for production.

### 3.2 Configurable Feature Toggles

The local experience should be modular. Proposed feature flags in a values file:

```yaml
kagenti:
  enabled: true

  features:
    istio:
      enabled: false        # Service mesh (Ambient mode)
    spire:
      enabled: false        # Zero-trust workload identity
    shipwright:
      enabled: false        # Container builds
    builds:
      enabled: false        # Build UI + Tekton
    observability:
      phoenix:
        enabled: true       # LLM trace viewer
      otel:
        enabled: false      # OpenTelemetry collector
      kiali:
        enabled: false      # Service mesh dashboard
    containerRegistry:
      enabled: false        # In-cluster registry
    certManager:
      enabled: false        # Certificate management
    mcpGateway:
      enabled: false        # MCP Gateway
```

**Minimal local setup** (fastest startup): Just kagenti operator + webhook + Keycloak. No Istio, no SPIRE, no builds.

**Full-featured setup**: Everything enabled, closest to production.

### 3.3 Keycloak Namespace

**Problem:** Agentstack deploys Keycloak in the same namespace as the server. Kagenti deploys it in a dedicated `keycloak` namespace. We need to converge.

**Options:**

#### Option A: Separate `keycloak` namespace (Recommended)
Move Keycloak to its own namespace, matching kagenti's approach.

**Pros:**
- Clean separation of concerns
- Matches kagenti convention
- Keycloak can be shared across agentstack + kagenti components
- Independent scaling and RBAC

**Cons:**
- Breaks single-chart deployment model
- Cross-namespace service discovery needed (trivial: `keycloak-service.keycloak.svc.cluster.local`)
- Need to coordinate Keycloak deployment between charts

**Implementation:**
- Remove Keycloak from agentstack Helm chart
- Use kagenti-deps chart to deploy Keycloak (or a standalone Keycloak chart)
- Update agentstack-server config to point to `keycloak-service.keycloak:8080`
- Both agentstack and kagenti configure their OAuth clients in the same realm

#### Option B: Keep in agentstack namespace, kagenti references it
Keep current setup, configure kagenti to use the existing Keycloak instance.

**Pros:**
- Minimal changes to agentstack
- Single chart still works

**Cons:**
- Non-standard for kagenti (may need chart modifications)
- Namespace coupling

#### Option C: Let kagenti-deps own Keycloak, agentstack consumes it
Kagenti-deps deploys Keycloak in `keycloak` namespace. Agentstack Helm chart declares Keycloak as disabled and references the external instance.

**Pros:**
- Clean ownership model
- Kagenti's Keycloak setup includes realm bootstrap, OAuth jobs, etc.

**Cons:**
- Deployment order dependency (keycloak must be up before agentstack)
- Agentstack still needs its own realm provisioning (see below)

**Decision:** **Option C** - Let kagenti-deps own Keycloak. Agentstack becomes a consumer. This is the cleanest separation.

**Helm chart implications:**
- This works fine even with multiple charts. The deployment order is:
  1. `helm install kagenti-deps` (includes Keycloak, optionally Istio, SPIRE, etc.)
  2. `helm install agentstack` (references Keycloak via service DNS)
  3. `helm install kagenti` (references Keycloak via service DNS)
- Or with an umbrella chart using `weight` annotations for ordering.

### 3.4 Keycloak Realm Provisioning

**Problem:** Both systems need Keycloak realm/client configuration. Moving Keycloak to kagenti-deps doesn't eliminate the need for agentstack's own realm bootstrapping.

**Agentstack's provision job** (`helm/templates/keycloak/provision-job.yaml`) does:
- Creates `agentstack` realm with custom login theme
- Creates roles: `agentstack-admin`, `agentstack-developer`
- Creates OAuth clients:
  - `agentstack-server` (confidential, service accounts + direct access grants)
  - `agentstack-ui` (confidential, standard flow + direct access grants)
  - `agentstack-cli` (public, standard flow + direct access grants, localhost redirect)
- Configures audience mappers per client (UI URL, API URL)
- Seeds users with passwords and role assignments

**Kagenti's realm setup** does:
- Creates `kagenti` realm (via Keycloak `autoBootstrapRealm`)
- Creates OAuth clients via Jobs: `kagenti-keycloak-client` (agents), `kagenti-ui-client` (UI), `kagenti-api` (API)
- Roles: `kagenti-admin`, `kagenti-operator`, `kagenti-viewer`

**Options for convergence:**

#### Option 1: Separate realms (DECIDED)
Keep `agentstack` realm and `kagenti` realm side by side. Each system provisions its own realm independently.

Kagenti uses a dedicated `kagenti` realm (configured via `keycloak_realm` in backend config, bootstrapped via `autoBootstrapRealm`). This is their own realm, not the master realm.

Agentstack keeps its own `agentstack` realm. Both realms live in the same Keycloak instance but are fully independent.

**Pros:**
- Zero coupling between the two provisioning jobs
- Each system owns its auth config completely
- Agentstack's provision-job.yaml stays unchanged (just point at new Keycloak URL)
- Clean separation - no risk of role/client name collisions

**Cons:**
- Users need accounts in both realms (or we configure identity brokering later)
- Two login flows if both UIs are deployed

#### Option 2: Shared realm (Future - Best for UX)
Merge into a single realm. One provision job creates all clients and roles.

#### Option 3: Separate realms + Identity Brokering (Future)
Each system has its own realm, but Keycloak brokers between them for SSO.

**Decision:** **Option 1** (separate realms). The provision job just needs its Keycloak URL updated from the local StatefulSet to `keycloak-service.keycloak:8080`. Everything else stays the same. We can evolve to Option 2 when we want unified SSO.

**What changes in the provision job:**
- Keep `provision-job.yaml` in the agentstack Helm chart
- Remove Keycloak StatefulSet, Service, and Secret templates (those move to kagenti-deps)
- Update the job to target the external Keycloak: `keycloak-service.keycloak:8080`
- Admin credentials need to be shared (either a shared secret or a dedicated admin client for provisioning)

---

## 4. Component Mapping

### What agentstack drops (delegates to kagenti)

| Agentstack Component | Kagenti Replacement |
|---|---|
| `KubernetesProviderDeploymentManager` | Kagenti operator deploys agents as standard K8s Deployments in team namespaces |
| `KubernetesProviderBuildManager` (Kaniko) | Shipwright + Tekton builds (optional) |
| Agent card in Docker labels (`beeai.dev.agent.json`) | Realtime HTTP fetch from `/.well-known/agent-card.json` |
| Agent card stored in DB | Realtime discovery from running agents |
| Scale-to-zero / auto-stop logic | Kagenti manages agent lifecycle (or standard HPA) |
| Provider model (managed/unmanaged distinction) | All agents are kagenti-managed Deployments |
| `build-provider-job.yaml` (Kaniko + Crane) | Shipwright BuildRun with Buildah strategy |
| Keycloak deployment | kagenti-deps Keycloak deployment |

### What agentstack keeps

| Component | Reason |
|---|---|
| A2A Proxy Service | Core routing/auth logic, user task tracking |
| Provider Registry sync | Can evolve to sync with kagenti's agent namespaces |
| PostgreSQL | Agentstack's own data (users, tasks, conversations) |
| Redis | Caching, rate limiting |
| SeaweedFS | Object storage for artifacts |
| Phoenix | LLM observability (kagenti also supports this) |

### What changes in agentstack-server

| Area | Change |
|---|---|
| `bootstrap.py` | Remove `KubernetesProviderDeploymentManager` and `KubernetesProviderBuildManager` injection |
| `providers.py` service | Rewrite to discover agents via kagenti API or direct K8s namespace scanning |
| `a2a.py` service | Update URL resolution: `http://{agent}.{namespace}.svc.cluster.local:8080` |
| Provider model | Simplify - remove `auto_stop_timeout`, `unmanaged_state`, build fields |
| Provider cron jobs | Remove `auto_stop_providers`, `refresh_unmanaged_provider_state`; keep or adapt registry sync |
| Configuration | Add kagenti connection settings, remove build/scaling config |

---

## 5. Multi-Tenancy, Agent Discovery, and Data Scoping

This is a critical design area. Agentstack currently has user-scoped data (conversations, tasks, files) but no namespace/team concept. Kagenti has namespace-based isolation but no per-user data scoping. We need to bridge these.

### 5.1 Current State

**Agentstack multi-tenancy:**
- User-per-tenant model: each user has isolated data via `created_by` FK
- Data scoped per-user: contexts, files, vector_stores, a2a_request_tasks, a2a_request_contexts
- Providers are semi-public: all users can read, only owner/devs can modify
- Model providers are fully global (no scoping)
- No organization/workspace/namespace abstraction
- Roles: ADMIN, DEVELOPER, USER (controls CRUD permissions, not visibility)

**Kagenti multi-tenancy:**
- Namespace-based: team namespaces (`team1`, `team2`) with `kagenti-enabled=true` label
- Role-based: `kagenti-admin` > `kagenti-operator` > `kagenti-viewer` (Keycloak realm roles)
- NO per-user namespace restrictions at the API level - all viewers see all enabled namespaces
- K8s RBAC on the backend service account controls what namespaces are actually accessible
- No user data storage (stateless - queries K8s API on every request)

### 5.2 Agent Discovery: How Should Agentstack Find Kagenti Agents?

#### Option A: Call Kagenti Backend API (DECIDED)

Agentstack calls `GET http://kagenti-backend.kagenti-system:8080/api/v1/agents?namespace=<ns>` to discover agents.

```
agentstack-server → HTTP → kagenti-backend → K8s API → Deployments with kagenti.io/type=agent
```

**Pros:**
- Clean separation - agentstack doesn't need K8s RBAC for agent namespaces
- Kagenti handles the label scanning, status aggregation, protocol detection
- Easier to evolve (kagenti can add caching, watching, CRDs without agentstack changes)
- Shared auth via Keycloak - agentstack can forward user tokens to kagenti API

**Cons:**
- Runtime dependency on kagenti backend being available
- Extra network hop
- Polling-based (kagenti has no watch/event mechanism either)

**Auth for kagenti API access:**
Agentstack-server will need a dedicated Keycloak client in the `kagenti` realm (e.g., `agentstack-api`) to authenticate against the kagenti backend API. This client would use client credentials grant (service-to-service). The kagenti provision job (or agentstack's provision job targeting the kagenti realm) needs to create this client with at least `kagenti-viewer` role.

**Implementation:**
```python
# New: KagentiAgentDiscovery service
class KagentiAgentDiscovery:
    def __init__(self, kagenti_url: str, token_provider: TokenProvider):
        self._url = kagenti_url  # http://kagenti-backend.kagenti-system:8080
        self._token_provider = token_provider  # client_credentials against kagenti realm

    async def list_agents(self, namespace: str | None = None) -> list[AgentSummary]:
        # GET /api/v1/agents?namespace={ns}
        # Authorization: Bearer <service-token>
        ...

    async def get_agent_card(self, namespace: str, name: str) -> AgentCard:
        # GET /api/v1/chat/{ns}/{name}/agent-card
        # (kagenti proxies to http://{name}.{ns}.svc:8080/.well-known/agent-card.json)
        ...
```

#### Option B: Direct K8s Label Scanning (Rejected)

Agentstack's service account scans Deployments with label `kagenti.io/type=agent` across namespaces.

**Why rejected:** K8s RBAC is namespace-scoped by default. Agentstack's service account in the `agentstack` namespace cannot list Deployments in `team1` or `team2` unless we grant it a ClusterRole. This is a significant RBAC escalation. An alternative would be deploying a "service agent" sidecar into each team namespace, but that adds complexity.

Note: this is a **K8s API RBAC** limitation, not a networking limitation. Network calls between namespaces always work (see section 5.6). But listing/watching resources across namespaces via the K8s API requires explicit RBAC grants.

#### Option C: K8s Watch + Local Cache (Future - Best for Production)

Same RBAC concern as Option B. Could be revisited if we add a ClusterRole for agentstack or use kagenti's operator to push events.

**Decision:** **Option A** (kagenti API). We will create a dedicated Keycloak client for agentstack-server in the kagenti realm to authenticate API calls.

### 5.3 Multi-Tenancy Model: Per-Namespace vs Global

The core question: **When a user opens agentstack, which agents do they see?**

#### Pattern 1: Global Agent Catalog + Per-User Data (Recommended)

All agents across all kagenti namespaces are visible to all agentstack users. User data (conversations, tasks, files) remains per-user as today.

```
Agents:        GLOBAL (all users see all agents from all namespaces)
Conversations: PER-USER (user's own chat history with agents)
Tasks:         PER-USER (A2A task ownership)
Files:         PER-USER (uploaded documents)
```

**When it makes sense:**
- Small teams, local development, PoC
- All agents are shared resources (like shared microservices)
- Users don't need to hide agents from each other
- Simplest to implement - mirrors current agentstack behavior

**Implementation:**
- Agentstack discovers all agents across all `kagenti-enabled=true` namespaces
- Provider list in agentstack UI shows agents grouped by namespace
- No changes to user model or data scoping

#### Pattern 2: Namespace-Scoped Agent Visibility

Users are assigned to namespaces (teams). They can only see/use agents in their namespaces.

```
Agents:        PER-NAMESPACE (user sees only agents in their team namespaces)
Conversations: PER-USER (within allowed namespaces)
Tasks:         PER-USER (within allowed namespaces)
Files:         PER-USER
```

**When it makes sense:**
- Multi-team environments
- Compliance/isolation requirements
- Different teams run different agent sets

**Implementation:**
- Add `user_namespaces` mapping (DB table or Keycloak groups → namespaces)
- Agentstack filters agent list by user's allowed namespaces
- Keycloak groups could map to kagenti namespaces (e.g., group `team1` → namespace `team1`)
- OR: Keycloak realm roles with namespace claims in JWT

**Keycloak integration approach:**
```
Keycloak realm: kagenti
├── Group: team1 → users who can access team1 namespace
├── Group: team2 → users who can access team2 namespace
└── Client: agentstack → includes group memberships in token claims
```

Agentstack reads group claims from JWT → maps to allowed namespaces → filters agent discovery.

#### Pattern 3: Hybrid - Global Catalog + Namespace Permissions

All agents are visible (catalog view), but users can only *interact* with agents in their namespaces.

```
Agent catalog:  GLOBAL (browse all agents)
Agent usage:    PER-NAMESPACE (chat only with agents in your namespaces)
Conversations:  PER-USER
```

**When it makes sense:**
- Users want to discover what's available but access is controlled
- Self-service model: "request access to namespace X"

**Recommendation for PoC:** Start with **Pattern 1** (global catalog). It matches current agentstack behavior and is simplest. Add namespace scoping later when we have real multi-team requirements.

### 5.4 DNS and URL Resolution

**Note on `localtest.me`:** We can adopt kagenti's `localtest.me` convention for simplicity. This wildcard DNS resolves `*.localtest.me` to `127.0.0.1`, which is useful for Keycloak redirect URIs, agent URLs, and UI access without `/etc/hosts` hacking.

Agent URL patterns:
- **In-cluster (service DNS):** `http://{agent-name}.{namespace}.svc.cluster.local:8080`
- **External (localtest.me):** `http://{agent-name}.{namespace}.localtest.me:8080` (requires ingress/port-forward)
- **Via kagenti API proxy:** `POST http://kagenti-backend.kagenti-system:8080/api/v1/chat/{ns}/{name}/send`
- **Via agentstack A2A proxy:** agentstack continues to proxy A2A requests, but resolves URLs to in-cluster service DNS

### 5.5 Auth Token Flow

Both systems use Keycloak. The question is whether agentstack forwards user tokens to agents or mints its own.

```
User → (Keycloak JWT) → agentstack-server → (???) → agent in team1 namespace
```

**Options:**
1. **Forward user token** - Agent receives the user's JWT. Agent can validate it against Keycloak. Simple but exposes user identity to agents.
2. **Token exchange** - Agentstack exchanges user token for a scoped service token (Keycloak token exchange). More secure, agents see a service identity.
3. **No auth to agents** (PoC) - Agents trust in-cluster traffic. Simplest for PoC, add auth later.

Kagenti's current approach: forwards the user's Authorization header to agents (option 1).

**Recommendation for PoC:** Option 3 (no auth to agents). Adopt option 1 or 2 when adding Istio/SPIRE.

### 5.6 Multi-Agent Communication

**Scenario:** Agent A needs to call Agent B. Both are in `team1` namespace. Agentstack runs in `agentstack` namespace. How should this work?

#### Networking: Cross-namespace is not a problem

Istio Ambient mode operates at the pod level, not namespace boundaries. Any pod can reach any service across namespaces via standard K8s DNS. Cross-namespace traffic gets automatic mTLS from the ztunnel layer.

```
agent-a.team1 → agent-b.team1                    # same namespace, trivial
agent-a.team1 → agent-b.team2.svc.cluster.local  # cross namespace, also fine
agent-a.team1 → agentstack-server.agentstack.svc  # cross namespace, fine
```

Access restrictions are opt-in via Istio policies:
- **AuthorizationPolicy**: "only SAs `agent-a` and `agent-b` in `team1` can communicate"
- **Waypoint proxies**: L7 policy enforcement (kagenti sets these up per agent namespace)
- **SPIRE identities**: each agent gets `spiffe://domain/ns/team1/sa/agent-a` for mutual authentication

#### The real question: should agent-to-agent go through agentstack?

**Option 1: Direct agent-to-agent (kagenti native)**
```
User → agentstack → Agent A → Agent B (direct, same namespace)
                           ↘ Agent C (direct, cross namespace)
```

- Agents discover each other via K8s DNS or agent cards
- Lowest latency, no bottleneck
- Istio + SPIRE handle auth and mTLS
- **Problem:** agentstack loses visibility. No audit trail, no task tracking, no rate limiting for agent-to-agent calls. Agentstack only sees the user→Agent A leg.

**Option 2: All traffic through agentstack proxy**
```
User → agentstack → Agent A
       agentstack ← Agent A (Agent A calls back to agentstack to reach Agent B)
       agentstack → Agent B
       agentstack ← Agent B (response)
       agentstack → Agent A (forwarded response)
```

- Full audit trail, task ownership tracking, token management
- Agentstack can enforce rate limits, quotas, access policies
- **Problem:** agentstack is a bottleneck and single point of failure for multi-agent workflows. Higher latency. Every agent-to-agent hop is 2 extra network hops.

**Option 3: Hybrid - agentstack for orchestration, direct for execution (Recommended)**
```
User → agentstack → Agent A (orchestrator)
                     Agent A → Agent B (direct, fast)
                     Agent A → Agent C (direct, fast)
                     Agent A → agentstack (report task status/results)
```

- Agentstack handles the user-facing session: auth, task creation, context management
- Agent A (the orchestrator) talks to sub-agents directly within the cluster
- Sub-agent calls use Istio mTLS + SPIRE identities for auth (no Keycloak tokens needed)
- Agentstack gets task results when the orchestrator reports back
- **Best of both worlds:** fast agent-to-agent, user-level tracking at the edges

**Istio policy example for namespace isolation:**
```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-intra-team
  namespace: team1
spec:
  action: ALLOW
  rules:
  - from:
    - source:
        namespaces: ["team1"]           # same namespace agents
    - source:
        namespaces: ["agentstack"]      # agentstack proxy
        principals: ["cluster.local/ns/agentstack/sa/agentstack-server"]
```

This allows agents within `team1` to talk freely to each other, and allows agentstack to call into `team1` agents. Cross-namespace agent-to-agent (e.g., `team1` → `team2`) would require explicit policy.

**Recommendation for PoC:** Option 2 (all through agentstack). Agentstack issues custom tokens and controls which agent can call which - this requires agentstack to remain in the request path. Direct agent-to-agent bypasses these controls. Option 3 can be explored later when we have Istio + SPIRE providing network-level identity and policy enforcement as an alternative to token-based control.

#### Cross-namespace communication: no architectural blockers

Regardless of which option we choose, **cross-namespace networking just works in K8s**. There is no restriction:

```
# Agent (team1) → agentstack API (agentstack namespace)
http://agentstack-server.agentstack.svc.cluster.local:8000/...  ← works

# Agentstack (agentstack namespace) → agent (team1)
http://weather-agent.team1.svc.cluster.local:8080/...  ← works

# Agent (team1) → agent (team2)
http://other-agent.team2.svc.cluster.local:8080/...  ← works
```

Namespaces are a logical boundary for resource organization and K8s RBAC, **not** a network boundary. Cross-namespace service DNS is a core K8s guarantee. Nothing in Istio, MicroShift, or kagenti changes this. Istio Ambient adds mTLS **on top** of existing connectivity - it doesn't restrict it. Restrictions are only created by explicit `NetworkPolicy` (K8s) or `AuthorizationPolicy` (Istio), and neither system creates deny-all policies by default.

**This means agentstack can safely live in its own namespace.** There is no architectural concern about agents calling back to agentstack or agentstack calling into agent namespaces.

---

## 6. Agent Card Discovery - New Model

(See also section 5.2 for discovery mechanism discussion)

### Current (agentstack)
```
Build time: agent-card.json → base64 → Docker label → stored in DB
Runtime: DB lookup → return cached card
Scale-to-zero: Card available even when agent is scaled down (from DB)
```

### New (kagenti-based)
```
Runtime: HTTP GET http://{agent}.{namespace}.svc:8080/.well-known/agent-card.json
Always-on: Agents must be running to serve their card
Alternative: Kagenti operator could maintain a card cache (future)
```

### Implications
- No more "offline" agents (agents scaled to zero can't serve cards)
- Discovery is always fresh (no stale cards)
- Agent list = `kubectl get deployments -l kagenti.io/type=agent` across namespaces
- Card validation happens at request time, not build time

### Transition Path
1. Keep DB-backed card cache as fallback during PoC
2. Add kagenti-based discovery as primary source
3. Remove DB cache once stable

---

## 7. Lima / MicroShift Integration

### Current Lima Setup
Agentstack uses Lima VMs with MicroShift for local development. The kagenti Helm charts need to install cleanly into this environment.

### Required Lima Changes
1. **Resource increase**: Kagenti components (especially Istio) need more RAM. Bump VM from current allocation.
2. **Port mappings**: Kagenti uses port 8080. Need to avoid conflicts or configure differently.
3. **DNS**: Adopt kagenti's `localtest.me` convention (wildcard DNS → 127.0.0.1). Simplifies Keycloak redirect URIs and agent access. See section 5.4.
4. **Image pre-pull**: Optional - pre-pull kagenti component images to speed up first startup.

### MicroShift Compatibility Notes
- MicroShift is a minimal OpenShift. Kagenti supports OpenShift via `global.openshift: true`.
- Some kagenti components use OLM (Operator Lifecycle Manager) for installation. MicroShift may not have OLM → need Helm-based alternatives.
- SPIRE's ZTWIM operator requires OCP 4.19+. MicroShift version needs checking. Alternative: `useSpireHelmChart: true`.
- Istio Ambient mode should work on MicroShift (it's standard K8s networking).

---

## 8. PoC Implementation Plan

### Phase 1: Minimal Integration (Week 1-2)
1. [ ] Install kagenti Helm charts into MicroShift (operator + webhook only)
2. [ ] Move Keycloak to separate namespace
3. [ ] Deploy a test agent via kagenti (manual kubectl)
4. [ ] Verify agent card discovery via HTTP
5. [ ] Update agentstack A2A proxy to route to kagenti-managed agents

### Phase 2: Feature Parity (Week 3-4)
6. [ ] Remove `KubernetesProviderDeploymentManager`
7. [ ] Remove `KubernetesProviderBuildManager`
8. [ ] Implement kagenti-based agent discovery in provider service
9. [ ] Update Helm chart (remove Keycloak, add kagenti-deps dependency)
10. [ ] Test full agent lifecycle: deploy → discover → chat → delete

### Phase 3: Optional Features (Week 5+)
11. [ ] Enable Istio Ambient mode
12. [ ] Enable SPIRE/SPIFFE identity
13. [ ] Enable Shipwright builds
14. [ ] Configure feature toggles in values.yaml
15. [ ] Performance testing with multiple agents across namespaces

---

## 9. Open Questions

1. **Kagenti operator on MicroShift**: Has this been tested? Any known issues?
2. **Agent namespaces**: Should agentstack create team namespaces, or delegate to kagenti?
3. **Auth flow**: Both systems use Keycloak OAuth. Do we need token exchange between agentstack and kagenti agents, or can we share the same realm/client?
4. **UI**: Do we keep agentstack UI only, or also deploy kagenti UI for agent management?
5. **MCP Gateway**: Agentstack has managed MCP service. Kagenti also has MCP Gateway. Which wins?
6. **Provider registry**: Current agentstack syncs from Git-based registries. Does kagenti have an equivalent, or do we keep this?
7. **Observability**: Both use Phoenix. Consolidate to one instance?
8. **Helm chart publishing**: Should we publish a combined chart, or keep them separate with documentation?

---

## 10. File Reference

### Agentstack - Key Files Modified/Removed
- `infrastructure/kubernetes/provider_deployment_manager.py` - **Removed**
- `infrastructure/kubernetes/provider_build_manager.py` - **Removed**
- `bootstrap.py` - **Modified** (removed build/deploy managers)
- `service_layer/services/providers.py` - **Simplified** (removed deployment manager, returns Provider directly)
- `service_layer/services/a2a.py` - **Simplified** (no deployment state checking)
- `domain/models/provider.py` - **Simplified** (removed managed/unmanaged, added source_type)
- `configuration.py` - **Modified** (added KagentiConfiguration)
- `infrastructure/kagenti/client.py` - **New** (kagenti API client)
- `jobs/crons/provider.py` - **Rewritten** (periodic kagenti agent sync)

### Kagenti - Key Files to Reference
- `.kagenti-temp/charts/kagenti/values.yaml` - Platform config
- `.kagenti-temp/charts/kagenti-deps/values.yaml` - Dependencies config (feature toggles)
- `.kagenti-temp/deployments/ansible/default_values.yaml` - Full default values
- `.kagenti-temp/kagenti/backend/app/routers/chat.py` - A2A implementation
- `.kagenti-temp/charts/kagenti-deps/templates/keycloak-k8s.yaml` - Keycloak deployment
