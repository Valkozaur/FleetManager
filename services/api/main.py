from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from .routers import ops, orders
import os

app = FastAPI(title="FleetManager API")

# Configure CORS
# Only enable CORS if explicitly requested (e.g. for local development)
# In production, CORS is typically handled by Nginx
if os.getenv("ENABLE_CORS", "false").lower() == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "https://dashboard.valdanktrading.org"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(ops.router)
app.include_router(orders.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
