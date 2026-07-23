from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.examples.candy import Solution

router = APIRouter()


class CandyRequest(BaseModel):
    ratings: list[int] = Field(..., min_length=1)


@router.post("/solve")
def solve_candy(body: CandyRequest):
    detail = Solution().candy_detail(body.ratings)
    return detail
