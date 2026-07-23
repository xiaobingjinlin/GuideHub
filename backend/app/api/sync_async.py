from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.examples.sync_async import run

router = APIRouter()


class SyncAsyncRequest(BaseModel):
    mode: str = Field(..., pattern="^(sync|async)$")


@router.post("/run")
def sync_async_run(body: SyncAsyncRequest):
    try:
        return run(body.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
