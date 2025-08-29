import uvicorn
from fastapi_app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )