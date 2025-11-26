from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Set
from uuid import UUID
from datetime import datetime, timezone

from ..schemas import RouteCreate, RouteResponse, StopCreate, StopResponse, RouteStatusUpdate, StopStatusUpdate, RouteStatus, DriverStatus, StopStatus, StopActivityType
from ..dependencies import get_db
from database_models.orm import Route, RouteStop, Driver, Truck

router = APIRouter(tags=["ops"])

@router.post("/routes/", response_model=RouteResponse)
async def create_route(route_in: RouteCreate, db: AsyncSession = Depends(get_db)):
    # Verify driver and truck exist
    driver = await db.get(Driver, route_in.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    truck = await db.get(Truck, route_in.truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    # Driver Conflict: Do not allow assigning a Route to a Driver who is already ON_ROUTE
    if driver.status == DriverStatus.ON_ROUTE:
         raise HTTPException(status_code=409, detail="Driver is already ON_ROUTE")

    new_route = Route(
        driver_id=route_in.driver_id,
        truck_id=route_in.truck_id,
        scheduled_start_at=route_in.scheduled_start_at,
        status=RouteStatus.PLANNED
    )
    db.add(new_route)
    await db.commit()
    await db.refresh(new_route)
    return new_route

@router.post("/routes/{route_id}/stops/batch", response_model=List[StopResponse])
async def add_stops_batch(route_id: UUID, stops_in: List[StopCreate], db: AsyncSession = Depends(get_db)):
    route = await db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    if route.status == RouteStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Cannot modify stops on an ACTIVE route")

    # Fetch existing stops to determine sequence and validate logic
    result = await db.execute(select(RouteStop).where(RouteStop.route_id == route_id).order_by(RouteStop.sequence_number))
    existing_stops = result.scalars().all()
    
    current_seq = 0
    picked_up_orders: Set[int] = set()
    
    if existing_stops:
        current_seq = existing_stops[-1].sequence_number
        for stop in existing_stops:
            if stop.activity_type == StopActivityType.PICKUP and stop.order_id:
                picked_up_orders.add(stop.order_id)

    new_stops = []
    for i, stop_data in enumerate(stops_in):
        seq_num = current_seq + i + 1
        
        if stop_data.activity_type == StopActivityType.PICKUP:
            if stop_data.order_id:
                picked_up_orders.add(stop_data.order_id)
        elif stop_data.activity_type == StopActivityType.DROP:
            if stop_data.order_id and stop_data.order_id not in picked_up_orders:
                raise HTTPException(status_code=400, detail=f"DROP for order {stop_data.order_id} without preceding PICKUP")
        
        new_stop = RouteStop(
            route_id=route_id,
            order_id=stop_data.order_id,
            sequence_number=seq_num,
            activity_type=stop_data.activity_type,
            status=StopStatus.PENDING,
            location=stop_data.location
        )
        new_stops.append(new_stop)
    
    db.add_all(new_stops)
    await db.commit()
    
    for stop in new_stops:
        await db.refresh(stop)
        
    return new_stops

@router.get("/routes/", response_model=List[RouteResponse])
async def get_routes(status: RouteStatus = None, db: AsyncSession = Depends(get_db)):
    query = select(Route)
    if status:
        query = query.where(Route.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/routes/{route_id}/status", response_model=RouteResponse)
async def update_route_status(route_id: UUID, status_update: RouteStatusUpdate, db: AsyncSession = Depends(get_db)):
    route = await db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    old_status = route.status
    new_status = status_update.status
    
    if old_status == new_status:
        return route

    driver = await db.get(Driver, route.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    if new_status == RouteStatus.ACTIVE:
        if driver.status == DriverStatus.ON_ROUTE:
             raise HTTPException(status_code=409, detail="Driver is already ON_ROUTE")
        driver.status = DriverStatus.ON_ROUTE
        db.add(driver)
        
    elif new_status == RouteStatus.COMPLETED:
        driver.status = DriverStatus.AVAILABLE
        db.add(driver)
    
    route.status = new_status
    db.add(route)
    
    try:
        await db.commit()
        await db.refresh(route)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    return route

@router.patch("/stops/{stop_id}/status", response_model=StopResponse)
async def update_stop_status(stop_id: UUID, status_update: StopStatusUpdate, db: AsyncSession = Depends(get_db)):
    stop = await db.get(RouteStop, stop_id)
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    stop.status = status_update.status
    if status_update.status == StopStatus.COMPLETED:
        stop.completed_at = datetime.now(timezone.utc)
        
    db.add(stop)
    await db.commit()
    await db.refresh(stop)
    return stop
