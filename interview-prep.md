# DevOps/SRE Interview Prep — Kartik

> Use this BEFORE the call. Glance, recall, close it. Don't open during the interview.

---

## 1. Core Concepts (know these cold)

### SRE vs DevOps
- **DevOps** = culture/practice: break silos, automate, ship fast safely.
- **SRE** = "class SRE implements DevOps" — enforces reliability via **error budgets**.
- **Error budget** = `1 - SLO`. E.g. 99.9% uptime → 43.2 min/month budget. Over budget → freeze features, focus on reliability.
- **SLI** (indicator: e.g. p99 latency) → **SLO** (target: p99 < 300ms) → **SLA** (contract: 99% or refund).

### Toil
- Manual, repetitive, automatable, devoid of enduring value, scales with traffic. Cap at <50% of SRE time.

### Incident response
- **Incident → mitigate → root-cause → postmortem (blameless)**.
- Mitigation first (rollback, scale up, shed load), root cause later.
- Postmortem: blameless, action items with owners + deadlines.

---

## 2. Linux

- **Process states**: R(running) S(sleep) D(uninterruptible sleep, usually I/O) Z(zombie) T(stopped).
- **Zombie**: child finished, parent hasn't called `wait()`. Kill parent or have it reap.
- **Load average**: avg runnable processes over 1/5/15 min. > #cores = saturation. (Includes D-state on Linux.)
- **OOM killer**: picks victim by `oom_score` (memory + runtime, root/`oom_score_adj` protected).
- **Signals**: `SIGTERM` (graceful), `SIGKILL` (uncatchable), `SIGHUP` (reload config), `SIGINT` (Ctrl-C).
- **File descriptors**: stdin=0, stdout=1, stderr=2. `ulimit -n` per process. `lsof`, `/proc/<pid>/fd`.
- **Nice**: -20 (high prio) to 19 (low prio). Root can lower.
- **systemd**: `systemctl status|start|restart|enable <svc>`, `journalctl -u <svc> -f`, units in `/etc/systemd/system/`.
- **cgroups/namespaces** = foundation of containers.
- Useful: `strace -p <pid>`, `sar -u`, `iostat -x 1`, `vmstat 1`, `ss -tlnp`, `netstat -tulpn`.

---

## 3. Networking

- **TCP handshake**: SYN → SYN-ACK → ACK. Close: FIN/ACK four-way.
- **TCP vs UDP**: TCP reliable/ordered/connected; UDP fire-and-forget, lower overhead.
- **Time wait**: ~60s after close, by closer, to catch delayed packets. `TIME_WAIT` pile-up → reuse ports / tune `tw_reuse`.
- **HTTP/2**: multiplexed streams over one TCP, header compression (HPACK), server push. Binary framing.
- **HTTP/3**: over QUIC (UDP), no head-of-line blocking, 0-RTT.
- **TLS handshake**: ClientHello → ServerHello+cert → key exchange → symmetric session key. TLS 1.3 = 1-RTT (0-RTT resumption).
- **DNS**: A (IPv4), AAAA (IPv6), CNAME (alias), MX (mail), TXT (SPF/DKIM/verification), NS, SOA. TTL controls caching.
- **Subnetting**: CIDR `/24` = 256 addresses (254 usable). `/16`=65k. `/30`=4 (2 usable).
- **NAT**: SNAT (outbound masquerade), DNAT (port forward), PAT (port-based, home routers).
- **Load balancer algorithms**: round-robin, least-conn, IP-hash, weighted, L4 (TCP) vs L7 (HTTP, cookie/path aware).
- **Reverse proxy vs forward proxy**: reverse sits in front of servers (nginx), forward in front of clients (corporate proxy).
- **CDN**: edge cache, TTL-based invalidation, origin shield, reduces RTT + origin load.

---

## 4. Docker

- **Image layers**: read-only, union FS (overlay2). Container = writable layer on top.
- **Dockerfile best practices**: small base (`alpine`/`slim`/`distroless`), multi-stage build, `.dockerignore`, one process per container, non-root user, pin versions, `CMD` vs `ENTRYPOINT`.
- **Multi-stage**: build in one image, copy artifact to slim runtime image. Shrinks image + removes build deps/secrets.
- **Volume vs bind mount**: volume (docker-managed, portable), bind mount (host path, dev only).
- **Network drivers**: bridge (default), host (no isolation), none, overlay (swarm/multi-host), macvlan.
- **`docker run` vs `docker-compose`**: compose = declarative multi-container, reproducible.
- **Image size tricks**: multi-stage, squash, `--no-install-recommends`, clean apt caches, distroless.
- **Security**: non-root user, read-only fs (`--read-only`), drop capabilities (`--cap-drop=ALL`), no `--privileged`, scan with Trivy/Grype.

---

## 5. Kubernetes

### Architecture
- **Control plane**: API server (only thing everything talks to), etcd (KV store, source of truth), scheduler (places pods), controller-manager (reconcile loops), kube-proxy (networking).
- **Worker node**: kubelet (pod agent), kube-proxy, container runtime (containerd).

### Key objects
- **Pod**: smallest deployable unit, 1+ containers shared network/storage.
- **Deployment**: declarative ReplicaSet + rolling update + rollback.
- **ReplicaSet**: ensures N pod replicas.
- **StatefulSet**: stable identity (pod-0, pod-1) + stable PVCs. For DBs.
- **DaemonSet**: one pod per node. Logging agents, CNI, node-exporter.
- **Service**: stable IP + DNS + LB across pods. ClusterIP (internal), NodePort, LoadBalancer, ExternalName.
- **Ingress**: L7 HTTP routing to services. Needs ingress controller (nginx, traefik, ALB).
- **ConfigMap/Secret**: config injection. Secret = base64 (NOT encrypted by default — enable encryption at rest + RBAC).
- **PVC/PV**: persistent storage. StorageClass for dynamic provisioning.
- **HPA**: horizontal pod autoscaler on CPU/mem/custom metrics. VPA = vertical (rare, restarts pod).
- **Namespace**: logical isolation + RBAC scope + resource quotas.

### Scheduling & lifecycle
- **Pod phases**: Pending → Running → Succeeded/Failed.
- **Probes**: `liveness` (restart if fail), `readiness` (remove from LB if fail), `startup` (disable others until ok).
- **Resources**: `requests` (scheduler) vs `limits` (cgroup cap). Set both. CPU=cores (millicores), Mem=Mi/Gi.
- **QoS classes**: Guaranteed (req=limit), Burstable (req<limit), BestEffort (none). Guaranteed evicted last.
- **Taints/tolerations**: repel pods / allow them. `NoSchedule`, `NoExecute`.
- **Affinity/anti-affinity**: co-locate or spread pods (e.g. DB pods on different nodes).
- **Node affinity** = hard/soft rules on node labels.

### Networking
- Every pod gets its own IP. CNI (Calico, Flannel, Cilium) handles pod-to-pod.
- **Service mesh** (Istio/Linkerd): mTLS, traffic shaping, observability via sidecar.
- **DNS**: `service.namespace.svc.cluster.local`. Headless service → pod A records.

### Operators & GitOps
- **Operator** = controller + CRD, encodes app operational knowledge (e.g. prometheus-operator).
- **GitOps** (ArgoCD/Flux): Git = source of truth, controller reconciles cluster to Git. Drift detection, audit, rollback = `git revert`.

### Common interview Q's
- **Rolling vs recreate vs blue-green vs canary**: rolling = zero-downtime gradual; recreate = downtime, simple; blue-green = instant switch, double resources; canary = % traffic, observe, ramp.
- **How does a pod get an IP?** CNI plugin assigns from pod CIDR, sets up veth pair, routes.
- **Pod stuck Pending?** Insufficient CPU/mem, no matching node (taints/affinity), PVC pending, image pull err, quota.
- **CrashLoopBackOff?** App crashing — check logs (`kubectl logs --previous`), config/secrets, missing deps, OOMKilled.
- **etcd backup**: `etcdctl snapshot save`. Critical — it's the cluster brain.

---

## 6. CI/CD

- **CI**: automated build+test on every push, fast feedback, merge often.
- **CD**: continuous delivery (deployable artifact ready) vs continuous deployment (auto-prod on green).
- **Pipeline stages**: lint → unit → build → integration → security scan (SAST/SCA) → package → deploy to staging → e2e → manual approval → prod → smoke test.
- **Artifact vs source**: deploy built artifact (image), not source. Immutable + traceable.
- **Trunk-based vs GitFlow**: trunk = small frequent merges to main + feature flags; GitFlow = release branches, heavier.
- **Feature flags**: decouple deploy from release. Canary, kill switch, A-B test.
- **Deployment safety**: blue-green, canary, progressive delivery (Flagger/Argo Rollouts), auto-rollback on metric regression.
- **Tools**: Jenkins (scripted, plugins), GitHub Actions (yaml, runners), GitLab CI, CircleCI, ArgoCD (GitOps), Spinnaker (multi-cloud canary).

---

## 7. Terraform / IaC

- **Declarative** (Terraform, CloudFormation) vs **imperative** (Ansible mostly, scripts).
- **State file**: maps real resources → config. Store in **remote backend** (S3+DynamoDB lock) — never commit locally, contains secrets.
- **`terraform plan/apply/destroy`**, `import` (adopt existing), `state mv/rm`, `workspace` (env isolation — or separate dirs).
- **Drift detection**: `plan` shows changes outside TF. Run periodically.
- **Modules**: reusable, versioned, inputs/outputs. Don't over-nest.
- **`count` vs `for_each`**: count=list index, for_each=map/set (safer for add/remove).
- **`lifecycle { prevent_destroy = true; create_before_destroy }`**.
- **Provider vs resource vs data source**: provider=API client, resource=managed thing, data source=read existing.
- **Pitfalls**: state in Git, no locking, huge monolithic state, secrets in state, no `depends_on` for implicit deps.
- **Ansible**: agentless, SSH, idempotent playbooks (YAML), roles, inventory. Good for config-mgmt + ad-hoc.

---

## 8. Cloud (AWS-leaning)

- **VPC**: subnet (public=internet GW, private=NAT GW), route tables, SG (stateful, instance-level) vs NACL (stateless, subnet-level).
- **IAM**: least privilege, roles for EC2 (no keys on boxes), MFA, policy JSON (Effect/Action/Resource/Condition).
- **S3**: object storage, 11x9 durability, buckets+keys, versions, lifecycle, encryption (SSE-S3/KMS), CORS, presigned URLs.
- **EBS vs EFS vs FSx**: EBS=block/instance, EFS=NFS/shared, FSx=Windows.
- **EC2 autoscaling**: ASG + launch template + ALB target. Scale on CloudWatch alarms.
- **ALB vs NLB**: ALB=L7 HTTP/HTTPS, host/path routing; NLB=L4 TCP/UDP, ultra-low latency, static IPs.
- **RDS**: managed SQL, multi-AZ HA, read replicas, automated backups + PITR.
- **Lambda**: serverless functions, 15min cap, cold start, triggers (API GW, SQS, EventBridge), pay per invocation.
- **SQS vs SNS vs Kinesis**: SQS=queue (decouple), SNS=pub/sub fanout, Kinesis=streaming (shards).
- **CloudFront**: CDN + edge compute (Lambda@Edge), WAF integration.
- **Cost**: rightsizing, RIs/Savings Plans, Spot for batch, lifecycle S3, NAT GW is expensive — route VPC endpoints.

---

## 9. Monitoring & Observability

- **Three pillars**: metrics (numbers over time), logs (events), traces (request path across services).
- **RED** (Rate, Errors, Duration) for services. **USE** (Utilization, Saturation, Errors) for resources.
- **Four golden signals** (Google): latency, traffic, errors, saturation.
- **Prometheus**: pull model, time series (`metric{labels}`), PromQL, labels=dimensions, `rate()`, `histogram_quantile()`.
- **Histogram vs summary**: histogram buckets → aggregatable p99 across instances; summary computes quantiles client-side (not aggregatable).
- **Grafana**: dashboards on Prometheus/Loki/Tempo/Jaeger/ES.
- **Alerting**: alert on symptoms (user impact) not causes. Avoid alert fatigue. Page only if user-visible + actionable.
- **Log levels**: DEBUG/INFO/WARN/ERROR. Structured logs (JSON) for searchability.
- **Distributed tracing**: trace ID propagated via headers (W3C traceparent), spans per service, find slowest hop.
- **OTel**: vendor-neutral instrumentation standard.

---

## 10. Security

- **Least privilege**, defense in depth, zero trust (never trust, always verify, mTLS).
- **Secrets**: Vault, AWS SM, Sealed Secrets, SOPS. Never in Git/images/env in plain.
- **Supply chain**: pin versions, SBOM, image scanning (Trivy/Grype), signed images (cosign), reproducible builds.
- **mTLS**: mutual cert auth between services. Service mesh makes it easy.
- **OWASP top 10**: injection, broken auth, sensitive data exposure, XXE, broken access control, security misconfig, XSS, insecure deserialization, known vulns, insufficient logging.
- **RBAC** in k8s: Role/ClusterRole + RoleBinding/ClusterBinding. ServiceAccount per app.

---

## 11. System Design (SRE-flavored)

### "Design a scalable web service that does X"
Framework:
1. **Clarify requirements** — functional + non-functional (RPS, latency, uptime, data size).
2. **Capacity estimate** — RPS, storage, bandwidth, CPU.
3. **High-level architecture** — client → CDN → LB → app → cache → DB → queue → workers.
4. **Deep dive** — data model, schema, indexes, caching strategy, async, scaling.
5. **Reliability** — SLOs, redundancy, failover, graceful degradation, circuit breakers, rate limiting.
6. **Trade-offs** — every choice has a cost; say it out loud.

### Key patterns
- **Cache-aside**: app reads cache, miss → DB → fill cache. TTL + invalidation.
- **CQRS**: separate read/write models. Reads from denormalized view.
- **Event sourcing**: store events, derive state. Audit + replay.
- **Circuit breaker**: fail fast when downstream down. half-open to probe recovery.
- **Rate limiting**: token bucket (bursty), leaky bucket (smooth), fixed/sliding window. Per-user + global.
- **Idempotency**: same op = same result. Critical for payments/retries. Use idempotency keys.
- **Backpressure**: slow consumer signals producer to slow down (queue depth, flow control).
- **Database scaling**: read replicas → sharding (hash/range) → partitioning. Sharding = operational cost.
- **CAP**: consistency/availability/partition tolerance — pick CP or AP under partition. Most web = AP + eventual consistency.

---

## 12. Behavioral (STAR — Situation, Task, Action, Result)

Prepare 5–6 stories you can flex into many questions:
1. **A production incident you led** — what broke, how you mitigated, postmortem, what you changed.
2. **A hard technical problem** — debugging, the "aha", the fix.
3. **A conflict with a teammate/manager** — how you resolved, kept respect.
4. **A time you failed** — owned it, learned, didn't repeat.
5. **An automation you built** — toil removed, hours saved, scale achieved.
6. **A time you pushed back on a deadline/feature for reliability** — error budget argument.

For each: **S** (context) → **T** (your responsibility) → **A** (what *you* did, "I" not "we") → **R** (measurable outcome: latency down X%, MTTR down Y min, toil down Z hrs/wk).

Common prompts: "Tell me about a time you... made a mistake / disagreed with your manager / worked under pressure / improved a process / mentored someone / handled an on-call nightmare."

---

## 13. Questions to ask THEM

- What's your on-call rotation like? (signal: do they burn people out)
- How is error budget enforced — who can say "no more deploys"?
- What's the biggest reliability problem you're trying to solve right now?
- How do SREs and product devs collaborate — embedded or platform team?
- What does success look like for this role in 6 months / 1 year?
- What's your CI/CD and deployment cadence?
- How do you handle toil — is it tracked and capped?

---

## 14. Last-minute mental checklist (60 sec before call)

- [ ] Camera at eye level, light in front of you, quiet room.
- [ ] Water nearby. Headphones.
- [ ] Tab with this file closed **before** the call starts.
- [ ] Slow breath. It's a two-way conversation, not an interrogation.
- [ ] If you don't know: "I haven't worked with X directly, but here's how I'd approach it..." then reason out loud. **Reasoning > recall.**
- [ ] Think out loud — they're assessing how you think, not just what you know.
- [ ] Ask clarifying questions before answering system design.

Good luck, Kartik. You've got this.
