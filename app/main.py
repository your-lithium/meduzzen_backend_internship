from fastapi import FastAPI
from routers import health_check
from core.config import AppConfig

config = AppConfig()

app = FastAPI()

app.include_router(health_check.router)

if __name__ == "__main__":
    host = config.HOST
    port = int(config.PORT)
    secret_key = config.SECRET_KEY
    import uvicorn
    uvicorn.run("main:app", host=host, port=port, reload=True)
