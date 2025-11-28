from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from typing import List, Set
from uuid import UUID
from datetime import datetime, timezone

from ..schemas import RouteCreate, RouteResponse, StopCreate, StopResponse, RouteStatusUpdate, StopStatusUpdate, RouteStatus, DriverStatus, StopStatus, StopActivityType, RoutePlanRequest, TruckStatus
from ..dependencies import get_db
from database_models.orm import Route, RouteStop, Driver, Truck, Order

router = APIRouter(tags=["ops"])

@router.post("/routes/", response_model=RouteResponse)
async def create_route(route_in: RouteCreate, db: AsyncSession = Depends(get_db)):
    """
    Legacy endpoint. Prefer /routes/plan.
    """
    truck = await db.get(Truck, route_in.truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    # Check if truck has a driver
    result = await db.execute(select(Driver).where(Driver.truck_id == truck.id))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=400, detail="Truck has no assigned driver")

    # Driver Conflict
    if driver.status == DriverStatus.ON_ROUTE:
         raise HTTPException(status_code=409, detail="Driver is already ON_ROUTE")
    
    # Basic name generation for legacy endpoint (fallback)
    date_str = route_in.scheduled_start_at.strftime("%Y%m%d")
    plate_clean = truck.plate_number.replace(" ", "").replace("-", "").upper()
    # Simple count for name uniqueness (not robust for concurrency here, but legacy)
    count_query = select(func.count()).select_from(Route).where(
        cast(Route.scheduled_start_at, Date) == route_in.scheduled_start_at.date(),
        Route.truck_id == truck.id
    )
    count_res = await db.execute(count_query)
    seq = count_res.scalar() + 1
    route_name = f"{date_str}-{plate_clean}-{seq}"

    new_route = Route(
        name=route_name,
        truck_id=route_in.truck_id,
        scheduled_start_at=route_in.scheduled_start_at,
        status=RouteStatus.PLANNED
    )
    db.add(new_route)
    await db.commit()
    await db.refresh(new_route)
    return new_route

@router.post("/routes/plan", response_model=RouteResponse)
async def create_route_plan(plan: RoutePlanRequest, db: AsyncSession = Depends(get_db)):
    # 1. Verify Truck
    # Lock Truck for sequence generation safety
    result = await db.execute(select(Truck).where(Truck.id == plan.truck_id).with_for_update())
    truck = result.scalars().first()
    
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    if not truck.is_active:
         raise HTTPException(status_code=400, detail="Truck is not active")

    # 2. Verify Driver
    result = await db.execute(select(Driver).where(Driver.truck_id == truck.id))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=400, detail="Truck has no assigned driver")

    # 3. Name Generation
    plate_clean = truck.plate_number.replace(" ", "").replace("-", "").upper()
    date_str = plan.date.strftime("%Y%m%d")
    
    # Count existing routes for this Truck + Date
    # Note: plan.date might be datetime, cast to date
    query = select(func.count()).select_from(Route).where(
        cast(Route.scheduled_start_at, Date) == plan.date.date(),
        Route.truck_id == truck.id
    )
    count_res = await db.execute(query)
    current_count = count_res.scalar() or 0
    seq = current_count + 1
    
    route_name = f"{date_str}-{plate_clean}-{seq}"
    
    # 4. Fetch Orders
    stmt = select(Order).where(Order.id.in_(plan.order_ids))
    orders_res = await db.execute(stmt)
    orders = orders_res.scalars().all()
    
    found_ids = {o.id for o in orders}
    missing = set(plan.order_ids) - found_ids
    if missing:
        raise HTTPException(status_code=404, detail=f"Orders not found: {missing}")
        
    # Sort orders to match input list order
    order_map = {o.id: o for o in orders}
    ordered_orders = [order_map[oid] for oid in plan.order_ids]

    # 5. Create Route
    new_route = Route(
        name=route_name,
        truck_id=truck.id,
        scheduled_start_at=plan.date,
        status=RouteStatus.PLANNED
    )
    db.add(new_route)
    await db.flush() # Get ID

    # 6. Create Stops
    stops = []
    seq_counter = 1
    
    for order in ordered_orders:
        # Stop A: Pickup
        pickup_loc = {
            "address": order.loading_address,
            "coordinates": order.loading_coordinates
        }
        stop_a = RouteStop(
            route_id=new_route.id,
            order_id=order.id,
            sequence_number=seq_counter,
            activity_type=StopActivityType.PICKUP,
            status=StopStatus.PENDING,
            location=pickup_loc
        )
        stops.append(stop_a)
        seq_counter += 1
        
        # Stop B: Drop
        drop_loc = {
            "address": order.unloading_address,
            "coordinates": order.unloading_coordinates
        }
        stop_b = RouteStop(
            route_id=new_route.id,
            order_id=order.id,
            sequence_number=seq_counter,
            activity_type=StopActivityType.DROP,
            status=StopStatus.PENDING,
            location=drop_loc
        )
        stops.append(stop_b)
        seq_counter += 1
        
    db.add_all(stops)
    
    try:
        await db.commit()
        await db.refresh(new_route)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create route: {str(e)}")

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

    # Find driver via truck
    # route.driver_id no longer exists. Need to find driver from truck_id
    result = await db.execute(select(Driver).where(Driver.truck_id == route.truck_id))
    driver = result.scalars().first()
    
    if not driver:
        # If no driver, we can't set to ACTIVE/ON_ROUTE generally, but maybe we can complete?
        # For now assume driver must exist
         raise HTTPException(status_code=404, detail="Driver not found for this route's truck")

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
