"""GuideHub FastAPI 入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import calculator, candy, concurrency

app = FastAPI(title="GuideHub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculator.router, prefix="/api/calculator", tags=["calculator"])
app.include_router(candy.router, prefix="/api/candy", tags=["candy"])
app.include_router(concurrency.router, prefix="/api/concurrency", tags=["concurrency"])


@app.get("/api/health")
def health():
    return {"ok": True}
