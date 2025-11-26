from fastapi import FastAPI
from .routers import ops

app = FastAPI(title="FleetManager API")

app.include_router(ops.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
