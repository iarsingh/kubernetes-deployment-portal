from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from portal.render import render

app = FastAPI(title="Kubernetes portal")


class Release(BaseModel):
    name: str
    image: str
    replicas: int = 2


@app.post("/releases")
def create_release(body: Release):
    try:
        manifest = render(body.name, body.image, body.replicas)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"applied": False, "manifest": manifest}
