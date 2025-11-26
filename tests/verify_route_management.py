import asyncio
import uuid
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.api.main import app
from services.api.dependencies import get_db
from database_models.orm import Base, Truck, Driver, Route, RouteStop, DriverStatus

# Configuration
DATABASE_URL = "postgresql+asyncpg://fleetmanager:fleetmanager_dev@localhost:5432/fleetmanager"

# Setup DB connection
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

async def verify():
    async with AsyncSessionLocal() as session:
        # 1. Setup Data
        print("Setting up test data...")
        truck = Truck(plate_number=f"TEST-{uuid.uuid4().hex[:6]}", capacity_weight=1000.0)
        driver = Driver(name="Test Driver", phone="555-0100", status=DriverStatus.AVAILABLE)
        session.add(truck)
        session.add(driver)
        await session.commit()
        await session.refresh(truck)
        await session.refresh(driver)
        print(f"Created Truck {truck.id} and Driver {driver.id}")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 2. Create Route
        print("\nTesting Create Route...")
        route_data = {
            "driver_id": str(driver.id),
            "truck_id": str(truck.id),
            "scheduled_start_at": datetime.now().isoformat()
        }
        response = await ac.post("/routes/", json=route_data)
        assert response.status_code == 200
        route = response.json()
        route_id = route["id"]
        print(f"Created Route {route_id} with status {route['status']}")

        # 3. Add Stops
        print("\nTesting Add Stops...")
        stops_data = [
            {
                "activity_type": "PICKUP",
                "order_id": 123,
                "location": {"lat": 40.7128, "lng": -74.0060, "address": "New York"}
            },
            {
                "activity_type": "DROP",
                "order_id": 123,
                "location": {"lat": 34.0522, "lng": -118.2437, "address": "Los Angeles"}
            }
        ]
        response = await ac.post(f"/routes/{route_id}/stops/batch", json=stops_data)
        if response.status_code != 200:
            print(f"Failed to add stops: {response.text}")
        assert response.status_code == 200
        stops = response.json()
        print(f"Added {len(stops)} stops")
        assert len(stops) == 2
        assert stops[0]["sequence_number"] == 1
        assert stops[1]["sequence_number"] == 2

        # 4. Test Validation (Drop without Pickup)
        print("\nTesting Validation (Invalid Drop)...")
        invalid_stops = [
            {
                "activity_type": "DROP",
                "order_id": 999,
                "location": {}
            }
        ]
        response = await ac.post(f"/routes/{route_id}/stops/batch", json=invalid_stops)
        assert response.status_code == 400
        print("Validation passed (got 400 as expected)")

        # 5. Activate Route
        print("\nTesting Route Activation...")
        response = await ac.patch(f"/routes/{route_id}/status", json={"status": "ACTIVE"})
        assert response.status_code == 200
        print("Route Activated")

        # Verify Driver Status
        async with AsyncSessionLocal() as session:
            d = await session.get(Driver, driver.id)
            print(f"Driver status is now: {d.status}")
            assert d.status == DriverStatus.ON_ROUTE

        # 6. Complete Stop
        print("\nTesting Stop Completion...")
        stop_id = stops[0]["id"]
        response = await ac.patch(f"/stops/{stop_id}/status", json={"status": "COMPLETED"})
        assert response.status_code == 200
        print("Stop Completed")

    print("\nVerification Successful!")

if __name__ == "__main__":
    asyncio.run(verify())
