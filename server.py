"""Amvera entrypoint: run FastAPI app via uvicorn."""
import os

import uvicorn


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("web:app", host="0.0.0.0", port=port, log_level="info")
