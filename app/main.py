from fastapi import FastAPI
import uvicorn

from routers import health_check
from core.config import config

app = FastAPI()

app.include_router(health_check.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
