from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
from uuid import UUID

from ..dependencies import get_db
from database_models.orm import Truck, Route, Driver, RouteStatus
from .. import schemas

router = APIRouter(
    prefix="/trucks",
    tags=["trucks"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.TruckResponse])
async def list_trucks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Truck).offset(skip).limit(limit)
    result = await db.execute(query)
    trucks = result.scalars().all()
    
    truck_responses = []
    for truck in trucks:
        # Check for active route to get assigned driver
        # This is a N+1 query, but acceptable for small scale. 
        # For production, we should join tables.
        route_query = select(Route).join(Driver).where(
            Route.truck_id == truck.id,
            Route.status.in_([RouteStatus.ACTIVE, RouteStatus.PLANNED])
        )
        route_result = await db.execute(route_query)
        active_route = route_result.scalars().first()
        
        assigned_driver_name = None
        if active_route:
            driver_query = select(Driver).where(Driver.id == active_route.driver_id)
            driver_result = await db.execute(driver_query)
            driver = driver_result.scalars().first()
            if driver:
                assigned_driver_name = driver.name

        truck_responses.append(
            schemas.TruckResponse(
                id=truck.id,
                plate_number=truck.plate_number,
                trailer_plate_number=truck.trailer_plate_number,
                capacity_weight=truck.capacity_weight,
                status=truck.status,
                is_active=truck.is_active,
                current_location="Los Angeles, CA", # Mocked
                assigned_driver=assigned_driver_name
            )
        )
    
    return truck_responses

@router.post("/", response_model=schemas.TruckResponse, status_code=status.HTTP_201_CREATED)
async def create_truck(
    truck: schemas.TruckCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if plate number already exists
    query = select(Truck).where(Truck.plate_number == truck.plate_number)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Truck with this license plate already exists"
        )
    
    new_truck = Truck(
        plate_number=truck.plate_number,
        trailer_plate_number=truck.trailer_plate_number,
        capacity_weight=truck.capacity_weight,
        status=truck.status
    )
    db.add(new_truck)
    await db.commit()
    await db.refresh(new_truck)
    
    return schemas.TruckResponse(
        id=new_truck.id,
        plate_number=new_truck.plate_number,
        trailer_plate_number=new_truck.trailer_plate_number,
        capacity_weight=new_truck.capacity_weight,
        status=new_truck.status,
        is_active=new_truck.is_active,
        current_location="Los Angeles, CA" # Mocked
    )

@router.get("/{truck_id}", response_model=schemas.TruckResponse)
async def get_truck(
    truck_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(Truck).where(Truck.id == truck_id)
    result = await db.execute(query)
    truck = result.scalars().first()
    
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
        
    # Get assigned driver logic (duplicated for now, could be refactored)
    route_query = select(Route).join(Driver).where(
        Route.truck_id == truck.id,
        Route.status.in_([RouteStatus.ACTIVE, RouteStatus.PLANNED])
    )
    route_result = await db.execute(route_query)
    active_route = route_result.scalars().first()
    
    assigned_driver_name = None
    if active_route:
        driver_query = select(Driver).where(Driver.id == active_route.driver_id)
        driver_result = await db.execute(driver_query)
        driver = driver_result.scalars().first()
        if driver:
            assigned_driver_name = driver.name

    return schemas.TruckResponse(
        id=truck.id,
        plate_number=truck.plate_number,
        trailer_plate_number=truck.trailer_plate_number,
        capacity_weight=truck.capacity_weight,
        status=truck.status,
        is_active=truck.is_active,
        current_location="Los Angeles, CA", # Mocked
        assigned_driver=assigned_driver_name
    )

@router.put("/{truck_id}", response_model=schemas.TruckResponse)
async def update_truck(
    truck_id: UUID,
    truck_update: schemas.TruckUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(Truck).where(Truck.id == truck_id)
    result = await db.execute(query)
    truck = result.scalars().first()
    
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    if truck_update.plate_number is not None:
        # Check uniqueness if changing plate
        if truck_update.plate_number != truck.plate_number:
            existing_query = select(Truck).where(Truck.plate_number == truck_update.plate_number)
            existing_result = await db.execute(existing_query)
            if existing_result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Truck with this license plate already exists"
                )
        truck.plate_number = truck_update.plate_number

    if truck_update.trailer_plate_number is not None:
        truck.trailer_plate_number = truck_update.trailer_plate_number
        
    if truck_update.capacity_weight is not None:
        truck.capacity_weight = truck_update.capacity_weight
        
    if truck_update.status is not None:
        truck.status = truck_update.status
        
    await db.commit()
    await db.refresh(truck)
    
    # Get assigned driver logic
    route_query = select(Route).join(Driver).where(
        Route.truck_id == truck.id,
        Route.status.in_([RouteStatus.ACTIVE, RouteStatus.PLANNED])
    )
    route_result = await db.execute(route_query)
    active_route = route_result.scalars().first()
    
    assigned_driver_name = None
    if active_route:
        driver_query = select(Driver).where(Driver.id == active_route.driver_id)
        driver_result = await db.execute(driver_query)
        driver = driver_result.scalars().first()
        if driver:
            assigned_driver_name = driver.name

    return schemas.TruckResponse(
        id=truck.id,
        plate_number=truck.plate_number,
        trailer_plate_number=truck.trailer_plate_number,
        capacity_weight=truck.capacity_weight,
        status=truck.status,
        is_active=truck.is_active,
        current_location="Los Angeles, CA", # Mocked
        assigned_driver=assigned_driver_name
    )

@router.delete("/{truck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_truck(
    truck_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(Truck).where(Truck.id == truck_id)
    result = await db.execute(query)
    truck = result.scalars().first()
    
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
        
    await db.delete(truck)
    await db.commit()
