import re

import yaml

NAME = re.compile(r"^[a-z]([a-z0-9-]{0,40}[a-z0-9])?$")
IMAGE = re.compile(r"^[a-z0-9][a-z0-9./_-]*:[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ENV_KEY = re.compile(r"^[A-Z_][A-Z0-9_]{0,63}$")
SECRET_KEYS = re.compile(r"(PASSWORD|SECRET|TOKEN|API_KEY|PRIVATE_KEY)")
PROFILES = {
    "small": {"requests": {"cpu": "100m", "memory": "128Mi"}, "limits": {"cpu": "500m", "memory": "256Mi"}},
    "medium": {"requests": {"cpu": "250m", "memory": "256Mi"}, "limits": {"cpu": "1", "memory": "512Mi"}},
    "large": {"requests": {"cpu": "500m", "memory": "512Mi"}, "limits": {"cpu": "2", "memory": "1Gi"}},
}


class RenderError(ValueError):
    pass


def validate(release):
    if not NAME.fullmatch(release["name"]):
        raise RenderError("name must be a DNS label: lowercase letters, digits, dashes, up to 42 characters")
    image = release["image"]
    if not IMAGE.fullmatch(image) or image.endswith(":latest"):
        raise RenderError("image tag latest is refused; pin repository:tag")
    if not 1 <= release["replicas"] <= 5:
        raise RenderError("replicas must be from 1 to 5")
    if release["profile"] not in PROFILES:
        raise RenderError("profile must be small, medium, or large")
    if not 1 <= release["port"] <= 65535:
        raise RenderError("port must be from 1 to 65535")
    for key in release["env"]:
        if not ENV_KEY.fullmatch(key):
            raise RenderError(f"env key {key} must be upper case letters, digits, underscores")
        if SECRET_KEYS.search(key):
            raise RenderError(f"env key {key} looks like a secret; mount a Secret instead of a literal value")


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
            "replicas": release["replicas"],
            "selector": {"matchLabels": {"app.kubernetes.io/name": name}},
            "template": {"metadata": {"labels": labels}, "spec": {"containers": [container]}},
        },
    }
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name, "labels": labels},
        "spec": {"selector": {"app.kubernetes.io/name": name}, "ports": [{"port": 80, "targetPort": "http"}]},
    }
    found = [deployment, service]
    if release["replicas"] >= 2:
        found.append(
            {
                "apiVersion": "policy/v1",
                "kind": "PodDisruptionBudget",
                "metadata": {"name": name, "labels": labels},
                "spec": {"minAvailable": 1, "selector": {"matchLabels": {"app.kubernetes.io/name": name}}},
            }
        )
    return found


def render(name, image, replicas, profile="small", port=8080, health_path="/healthz", env=None):
    release = {
        "name": name,
        "image": image,
        "replicas": replicas,
        "profile": profile,
        "port": port,
        "health_path": health_path,
        "env": env or {},
    }
    return yaml.safe_dump_all(objects(release), sort_keys=False)


def helm_values(name, image, replicas, profile="small"):
    repository, tag = image.rsplit(":", 1)
    return yaml.safe_dump(
        {"nameOverride": name, "image": {"repository": repository, "tag": tag}, "replicas": replicas, "resources": PROFILES[profile]},
        sort_keys=False,
    )
