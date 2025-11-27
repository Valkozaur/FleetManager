from fastapi import FastAPI
from .routers import ops, orders

app = FastAPI(title="FleetManager API")

# CORS is handled by nginx reverse proxy - no need to duplicate here

app.include_router(ops.router)
app.include_router(orders.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
