from fastapi import FastAPI
from .routers import ops, orders

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FleetManager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ops.router)
app.include_router(orders.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
