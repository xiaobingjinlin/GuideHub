from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.examples.concurrency import run_cpu, run_io

router = APIRouter()


class ConcurrencyRequest(BaseModel):
    mode: str = Field(..., pattern="^(serial|threads|processes)$")


@router.post("/io")
def concurrency_io(body: ConcurrencyRequest):
    try:
        return run_io(body.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/cpu")
def concurrency_cpu(body: ConcurrencyRequest):
    try:
        return run_cpu(body.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
