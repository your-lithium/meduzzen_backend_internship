from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {
              "status_code": 200,
              "detail": "ok",
              "result": "working"
            }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)
