from backend.config import HOST, PORT
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True, log_level="info")
