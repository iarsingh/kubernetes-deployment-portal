# kubernetes-deployment-portal — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does kubernetes-deployment-portal address, and what can you demonstrate?

The form asks for a name, a pinned image, replicas, a resource profile, and a port. The API returns a Deployment, a Service, and a PodDisruptionBudget when there are two or more replicas, plus matching Helm values. `applied` is false: this portal does not call the cluster.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/portal/main.py`](src/portal/main.py): User interface code/assets.
- [`src/portal/render.py`](src/portal/render.py): User interface code/assets.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`web/src/App.tsx`](web/src/App.tsx): User interface code/assets.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.
- [`tests/test_portal.py`](tests/test_portal.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `objects` and explain the decision it makes?

The main walkthrough here is `objects(release)` in [`src/portal/render.py`](src/portal/render.py#L39).

```python
def objects(release):
    validate(release)
    name = release["name"]
    labels = {"app.kubernetes.io/name": name, "app.kubernetes.io/managed-by": "deployment-portal"}
    container = {
        "name": name,
        "image": release["image"],
        "ports": [{"containerPort": release["port"], "name": "http"}],
        "resources": PROFILES[release["profile"]],
        "readinessProbe": {"httpGet": {"path": release["health_path"], "port": "http"}, "periodSeconds": 10},
        "livenessProbe": {"httpGet": {"path": release["health_path"], "port": "http"}, "initialDelaySeconds": 15},
        "securityContext": {"runAsNonRoot": True, "allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True},
    }
    if release["env"]:
        container["env"] = [{"name": key, "value": str(value)} for key, value in sorted(release["env"].items())]
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "labels": labels},
        "spec": {
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `found.append`, `release['env'].items`, `sorted`, `str`, `validate`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `validate` have?

`validate(release)` is defined in [`src/portal/render.py`](src/portal/render.py#L20).

It uses `ENV_KEY.fullmatch`, `IMAGE.fullmatch`, `NAME.fullmatch`, `RenderError`, `SECRET_KEYS.search`, `image.endswith`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=422, detail=str(exc))` in [`src/portal/main.py`](src/portal/main.py#L34).
- `RenderError('name must be a DNS label: lowercase letters, digits, dashes, up to 42 characters')` in [`src/portal/render.py`](src/portal/render.py#L22).
- `RenderError('image tag latest is refused; pin repository:tag')` in [`src/portal/render.py`](src/portal/render.py#L25).
- `RenderError('replicas must be from 1 to 5')` in [`src/portal/render.py`](src/portal/render.py#L27).
- `RenderError('profile must be small, medium, or large')` in [`src/portal/render.py`](src/portal/render.py#L29).
- `RenderError('port must be from 1 to 65535')` in [`src/portal/render.py`](src/portal/render.py#L31).
- `RenderError(f'env key {key} must be upper case letters, digits, underscores')` in [`src/portal/render.py`](src/portal/render.py#L34).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_portal.py`](tests/test_portal.py#L18) contains `test_latest_is_refused_and_limits_are_rendered`:

```python
def test_latest_is_refused_and_limits_are_rendered():
    assert release(image="billing:latest").status_code == 422
    body = release().json()
    assert body["applied"] is False
    assert "cpu: 100m" in body["manifest"]
    assert ":latest" not in body["manifest"]
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/portal/main.py`](src/portal/main.py#L20).
- `GET /profiles` → `profiles` in [`src/portal/main.py`](src/portal/main.py#L25).
- `POST /releases` → `create_release` in [`src/portal/main.py`](src/portal/main.py#L30).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `PROFILES` in [`src/portal/render.py`](src/portal/render.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `objects`?

In [`src/portal/render.py`](src/portal/render.py#L39), `objects(release)` receives the inputs. The function computes these intermediate values:

- `name = release['name']`
- `labels = {'app.kubernetes.io/name': name, 'app.kubernetes.io/managed-by': 'deployment-portal'}`
- `container = {'name': name, 'image': release['image'], 'ports': [{'containerPort': release['port'], 'name': 'http'}], 'resources': PROFILES[release['profile']], 'readinessProbe': {'httpGet': {'path': release['health_path'], 'port': 'http'}, 'periodSeconds': 10}, 'livenessProbe': {'httpGet': {'path': release['health_path'], 'port': 'http'}, 'initialDelaySeconds': 15}, 'securityContext': {'runAsNonRoot': True, 'allowPrivilegeEscalation': False, 'rea`
- `deployment = {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': name, 'labels': labels}, 'spec': {'replicas': release['replicas'], 'selector': {'matchLabels': {'app.kubernetes.io/name': name}}, 'template': {'metadata': {'labels': labels}, 'spec': {'containers': [container]}}}}`
- `service = {'apiVersion': 'v1', 'kind': 'Service', 'metadata': {'name': name, 'labels': labels}, 'spec': {'selector': {'app.kubernetes.io/name': name}, 'ports': [{'port': 80, 'targetPort': 'http'}]}}`
- `found = [deployment, service]`

Its result is defined by:

- `found`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/portal/render.py`](src/portal/render.py#L39) branches on:

- `release['env']`
- `release['replicas'] >= 2`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 14. What does `web/src/App.tsx` own?

[`web/src/App.tsx`](web/src/App.tsx) defines `App`, `submit`. Its imports include `react`.

Trace these definitions and imports to explain the module boundary. Relative imports identify project code; package imports should be checked against the nearest manifest.
