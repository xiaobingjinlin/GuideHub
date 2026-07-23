from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.examples.file_io import append_line, get_content, reset_content

router = APIRouter()


class AppendRequest(BaseModel):
    line: str | None = Field(default=None, description="要写入的一句话；默认用示例句")


@router.get("/content")
def file_io_content():
    return get_content()


@router.post("/append")
def file_io_append(body: AppendRequest | None = None):
    line = body.line if body else None
    return append_line(line)


@router.post("/reset")
def file_io_reset():
    return reset_content()
