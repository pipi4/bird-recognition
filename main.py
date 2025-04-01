from fastapi import FastAPI
from uvicorn import Server, Config
from routers.yolo import router
import os

app = FastAPI()

app.include_router(router)

@app.get("/")
def get_index():
    return {"message": "Welcome to the FastAPI application!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = Server(Config(app, host="0.0.0.0", port=port))
    server.run()
