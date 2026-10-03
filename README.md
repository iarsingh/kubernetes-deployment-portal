# Kubernetes deployment portal

Level: Intermediate

Skills: React, FastAPI, Kubernetes, Helm

The form asks for a name, an image, and a replica count. The API returns a Deployment manifest with CPU and memory limits. An image tagged `latest` is refused. `applied` is false: this portal does not call the cluster.

`helm/service` is the chart shape for the same values. `web/src/App.tsx` posts to `/releases`.

```bash
pip install -r requirements.txt
pytest -q
```

