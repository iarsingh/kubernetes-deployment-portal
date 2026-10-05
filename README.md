# Kubernetes deployment portal

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/portal/main.py`](src/portal/main.py) | HTTP handlers: `GET /healthz`, `GET /profiles`, `POST /releases` |
| [`src/portal/render.py`](src/portal/render.py) | Functions: `validate`, `objects`, `render`, `helm_values` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`web/src/App.tsx`](web/src/App.tsx) | User interface code/assets |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_portal.py`](tests/test_portal.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn portal.main:app --reload
```

<!-- project-guide:end -->

Level: Intermediate

Skills: React, FastAPI, Kubernetes, Helm, manifest validation

The form asks for a name, a pinned image, replicas, a resource profile, and a port. The API returns a Deployment, a Service, and a PodDisruptionBudget when there are two or more replicas, plus matching Helm values. `applied` is false: this portal does not call the cluster.

The manifest is built as data and serialized with PyYAML, so it is always valid YAML and the Deployment `selector` always matches the pod labels.

```bash
pip install -r requirements.txt
pytest -q
docker compose up --build
```

```bash
curl -s -X POST localhost:8000/releases -H 'content-type: application/json' \
  -d '{"name":"billing","image":"billing:0.1.0","replicas":2,"profile":"small","env":{"LOG_LEVEL":"info"}}'
```

| Profile | Requests | Limits |
| --- | --- | --- |
| small | 100m CPU, 128Mi | 500m CPU, 256Mi |
| medium | 250m CPU, 256Mi | 1 CPU, 512Mi |
| large | 500m CPU, 512Mi | 2 CPU, 1Gi |

Every container gets readiness and liveness probes on `health_path`, `runAsNonRoot`, no privilege escalation, and a read-only root filesystem.

## What it refuses

- An image tagged `latest`, or with no tag.
- A name that is not a DNS label. A newline cannot smuggle extra YAML into the manifest.
- Replicas outside 1 to 5, or an unknown profile.
- An environment variable whose name looks like a secret (`PASSWORD`, `SECRET`, `TOKEN`, `API_KEY`, `PRIVATE_KEY`). Mount a Secret instead of putting the value in the manifest.

`helm/service` is the chart shape for the same values. `web/src/App.tsx` renders the manifest and the values side by side.
