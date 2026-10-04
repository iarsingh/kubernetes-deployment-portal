import yaml
from fastapi.testclient import TestClient

from portal.main import app

client = TestClient(app)


def release(**overrides):
    body = {"name": "billing", "image": "billing:0.1.0", "replicas": 2, **overrides}
    return client.post("/releases", json=body)


def documents(response):
    return list(yaml.safe_load_all(response.json()["manifest"]))


def test_latest_is_refused_and_limits_are_rendered():
    assert release(image="billing:latest").status_code == 422
    body = release().json()
    assert body["applied"] is False
    assert "cpu: 100m" in body["manifest"]
    assert ":latest" not in body["manifest"]


def test_selector_matches_the_pod_labels():
    deployment = documents(release())[0]
    selector = deployment["spec"]["selector"]["matchLabels"]
    pod_labels = deployment["spec"]["template"]["metadata"]["labels"]
    assert selector.items() <= pod_labels.items()


def test_service_and_pdb_are_rendered_for_two_replicas():
    kinds = [doc["kind"] for doc in documents(release(replicas=2))]
    assert kinds == ["Deployment", "Service", "PodDisruptionBudget"]
    assert [doc["kind"] for doc in documents(release(replicas=1))] == ["Deployment", "Service"]


def test_container_runs_as_non_root_with_probes():
    container = documents(release())[0]["spec"]["template"]["spec"]["containers"][0]
    assert container["securityContext"]["runAsNonRoot"] is True
    assert container["readinessProbe"]["httpGet"]["path"] == "/healthz"


def test_profile_changes_the_resources():
    container = documents(release(profile="large"))[0]["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["limits"]["memory"] == "1Gi"
    assert release(profile="huge").status_code == 422


def test_newline_in_name_cannot_inject_yaml():
    assert release(name="billing\n  namespace: kube-system").status_code == 422


def test_secret_looking_env_is_refused():
    response = release(env={"DB_PASSWORD": "hunter2"})
    assert response.status_code == 422
    assert "mount a Secret" in response.json()["detail"]
    env = documents(release(env={"LOG_LEVEL": "info"}))[0]["spec"]["template"]["spec"]["containers"][0]["env"]
    assert env == [{"name": "LOG_LEVEL", "value": "info"}]


def test_replicas_outside_one_to_five_are_refused():
    assert release(replicas=0).status_code == 422
    assert release(replicas=6).status_code == 422


def test_helm_values_split_repository_and_tag():
    values = yaml.safe_load(release().json()["helm_values"])
    assert values["image"] == {"repository": "billing", "tag": "0.1.0"}
