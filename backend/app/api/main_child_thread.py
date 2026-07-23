from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.examples.main_child_thread import run

router = APIRouter()


class MainChildRequest(BaseModel):
    mode: str = Field(..., pattern="^(single|main_child)$")


@router.post("/run")
def main_child_run(body: MainChildRequest):
    try:
        return run(body.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
