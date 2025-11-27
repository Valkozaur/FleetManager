from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
from uuid import UUID

from ..dependencies import get_db
from database_models.orm import Driver, Truck, DriverStatus
from .. import schemas

router = APIRouter(
    prefix="/drivers",
    tags=["drivers"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.DriverResponse])
async def list_drivers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Driver).offset(skip).limit(limit)
    result = await db.execute(query)
    drivers = result.scalars().all()
    
    driver_responses = []
    for driver in drivers:
        assigned_truck_plate = None
        if driver.truck_id:
            truck_query = select(Truck).where(Truck.id == driver.truck_id)
            truck_result = await db.execute(truck_query)
            truck = truck_result.scalars().first()
            if truck:
                assigned_truck_plate = truck.plate_number

        driver_responses.append(
            schemas.DriverResponse(
                id=driver.id,
                name=driver.name,
                phone=driver.phone,
                status=driver.status,
                truck_id=driver.truck_id,
                assigned_truck_plate=assigned_truck_plate
            )
        )
    
    return driver_responses

@router.post("/", response_model=schemas.DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver: schemas.DriverCreate,
    db: AsyncSession = Depends(get_db)
):
    new_driver = Driver(
        name=driver.name,
        phone=driver.phone,
        status=driver.status,
        truck_id=driver.truck_id
    )
    db.add(new_driver)
    await db.commit()
    await db.refresh(new_driver)
    
    assigned_truck_plate = None
    if new_driver.truck_id:
        truck_query = select(Truck).where(Truck.id == new_driver.truck_id)
        truck_result = await db.execute(truck_query)
        truck = truck_result.scalars().first()
        if truck:
            assigned_truck_plate = truck.plate_number
            
    return schemas.DriverResponse(
        id=new_driver.id,
        name=new_driver.name,
        phone=new_driver.phone,
        status=new_driver.status,
        truck_id=new_driver.truck_id,
        assigned_truck_plate=assigned_truck_plate
    )

@router.get("/{driver_id}", response_model=schemas.DriverResponse)
async def get_driver(
    driver_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(Driver).where(Driver.id == driver_id)
    result = await db.execute(query)
    driver = result.scalars().first()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
        
    assigned_truck_plate = None
    if driver.truck_id:
        truck_query = select(Truck).where(Truck.id == driver.truck_id)
        truck_result = await db.execute(truck_query)
        truck = truck_result.scalars().first()
        if truck:
            assigned_truck_plate = truck.plate_number

    return schemas.DriverResponse(
        id=driver.id,
        name=driver.name,
        phone=driver.phone,
        status=driver.status,
        truck_id=driver.truck_id,
        assigned_truck_plate=assigned_truck_plate
    )

@router.put("/{driver_id}", response_model=schemas.DriverResponse)
async def update_driver(
    driver_id: UUID,
    driver_update: schemas.DriverUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(Driver).where(Driver.id == driver_id)
    result = await db.execute(query)
    driver = result.scalars().first()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    if driver_update.name is not None:
        driver.name = driver_update.name
        
    if driver_update.phone is not None:
        driver.phone = driver_update.phone
        
    if driver_update.status is not None:
        driver.status = driver_update.status
        
    if driver_update.truck_id is not None:
        # Validate truck exists
        truck_query = select(Truck).where(Truck.id == driver_update.truck_id)
        truck_result = await db.execute(truck_query)
        if not truck_result.scalars().first():
             raise HTTPException(status_code=404, detail="Truck not found")
        driver.truck_id = driver_update.truck_id
        
    await db.commit()
    await db.refresh(driver)
    
    assigned_truck_plate = None
    if driver.truck_id:
        truck_query = select(Truck).where(Truck.id == driver.truck_id)
        truck_result = await db.execute(truck_query)
        truck = truck_result.scalars().first()
        if truck:
            assigned_truck_plate = truck.plate_number

    return schemas.DriverResponse(
        id=driver.id,
        name=driver.name,
        phone=driver.phone,
        status=driver.status,
        truck_id=driver.truck_id,
        assigned_truck_plate=assigned_truck_plate
    )

@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    driver_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(Driver).where(Driver.id == driver_id)
    result = await db.execute(query)
    driver = result.scalars().first()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
        
    await db.delete(driver)
    await db.commit()

@router.post("/{driver_id}/assign_truck", response_model=schemas.DriverResponse)
async def assign_truck(
    driver_id: UUID,
    truck_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Get driver
    driver_query = select(Driver).where(Driver.id == driver_id)
    driver_result = await db.execute(driver_query)
    driver = driver_result.scalars().first()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Get truck
    truck_query = select(Truck).where(Truck.id == truck_id)
    truck_result = await db.execute(truck_query)
    truck = truck_result.scalars().first()
    
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
        
    driver.truck_id = truck.id
    await db.commit()
    await db.refresh(driver)
    
    return schemas.DriverResponse(
        id=driver.id,
        name=driver.name,
        phone=driver.phone,
        status=driver.status,
        truck_id=driver.truck_id,
        assigned_truck_plate=truck.plate_number
    )
