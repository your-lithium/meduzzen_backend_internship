from fastapi import FastAPI
from routers import health_check
from core.config import AppConfig

secret_key = AppConfig.SECRET_KEY
database_url = AppConfig.DATABASE_URL
port = AppConfig.PORT

app = FastAPI()

app.include_router(health_check.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)
