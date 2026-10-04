from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from portal.render import PROFILES, RenderError, helm_values, render

app = FastAPI(title="Kubernetes portal")


class Release(BaseModel):
    name: str
    image: str
    replicas: int = 2
    profile: str = "small"
    port: int = 8080
    health_path: str = Field(default="/healthz", pattern=r"^/[A-Za-z0-9/_-]*$")
    env: dict[str, str] = Field(default_factory=dict)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/profiles")
def profiles():
    return {"profiles": PROFILES}


@app.post("/releases")
def create_release(body: Release):
    try:
        manifest = render(body.name, body.image, body.replicas, body.profile, body.port, body.health_path, body.env)
    except RenderError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "applied": False,
        "manifest": manifest,
        "helm_values": helm_values(body.name, body.image, body.replicas, body.profile),
    }
