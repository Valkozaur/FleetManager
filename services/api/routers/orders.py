from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..dependencies import get_db
from database_models.orm import Order, Route, RouteStop, StopActivityType, RouteStatus, StopStatus
from pydantic import BaseModel

router = APIRouter(tags=["orders"])

class OrderResponse(BaseModel):
    id: int
    email_id: str
    customer: Optional[str] = None # Mapped from email_sender for now
    loading_address: str
    unloading_address: str
    loading_date: datetime
    unloading_date: datetime
    status: str
    
    class Config:
        from_attributes = True

@router.get("/orders/", response_model=List[OrderResponse])
async def get_orders(db: AsyncSession = Depends(get_db)):
    """
    Fetch all orders with their derived status.
    """
    # We need to join Order with RouteStop and Route to determine status
    # This is a bit complex because an order might not be in a route, or might be in a completed route.
    # Logic:
    # 1. Fetch all orders.
    # 2. For each order, check if it's associated with any RouteStop.
    # 3. If no RouteStop -> PENDING
    # 4. If RouteStop exists:
    #    - Check the Route status.
    #    - If Route is PLANNED -> ASSIGNED
    #    - If Route is ACTIVE -> IN_TRANSIT
    #    - If Route is COMPLETED -> COMPLETED
    #    - Also check if the specific DROP stop is COMPLETED -> COMPLETED
    
    # Efficient query:
    # Select Order and the latest RouteStop/Route info associated with it.
    # Since an order could theoretically be in multiple routes (re-delivery?), we take the latest.
    # For MVP, assuming 1:1 or 1:N where latest matters.
    
    stmt = (
        select(Order, Route.status, RouteStop.status)
        .outerjoin(RouteStop, Order.id == RouteStop.order_id)
        .outerjoin(Route, RouteStop.route_id == Route.id)
        .order_by(Order.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    orders_resp = []
    seen_orders = set()
    
    for row in rows:
        order, route_status, stop_status = row
        
        if order.id in seen_orders:
            continue
        seen_orders.add(order.id)
        
        status = "Pending"
        
        if route_status:
            if route_status == RouteStatus.PLANNED:
                status = "Assigned"
            elif route_status == RouteStatus.ACTIVE:
                status = "In Transit"
            elif route_status == RouteStatus.COMPLETED:
                status = "Completed"
            
            # Override if the specific drop stop is completed (though usually route completed implies this)
            # But maybe route is active but this specific order is dropped off?
            # We need to check the DROP stop status specifically if we want that granularity.
            # The join above gives us *a* stop. If there are multiple stops for an order (pickup + drop),
            # we might get either.
            # Let's refine the query to prefer the DROP stop status if available, or just rely on Route status for now.
            
            if stop_status == StopStatus.COMPLETED:
                 status = "Completed"

        orders_resp.append(OrderResponse(
            id=order.id,
            email_id=order.email_id,
            customer=order.email_sender, # Using sender as customer for now
            loading_address=order.loading_address,
            unloading_address=order.unloading_address,
            loading_date=order.loading_date,
            unloading_date=order.unloading_date,
            status=status
        ))
        
    return orders_resp

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_details(order_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch a single order by ID with its derived status.
    """
    stmt = (
        select(Order, Route.status, RouteStop.status)
        .outerjoin(RouteStop, Order.id == RouteStop.order_id)
        .outerjoin(Route, RouteStop.route_id == Route.id)
        .where(Order.id == order_id)
    )
    
    stmt = (
        select(Order, Route.status, RouteStop.status)
        .outerjoin(RouteStop, Order.id == RouteStop.order_id)
        .outerjoin(Route, RouteStop.route_id == Route.id)
        .where(Order.id == order_id)
    )
    
    result = await db.execute(stmt)
    # There might be multiple rows if an order is associated with multiple stops (e.g. pickup and drop)
    # We need to aggregate them to determine the overall status.
    rows = result.all()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Logic to determine status from potentially multiple rows (stops)
    # Similar to list view, but we have all rows for this order.
    
    order = rows[0][0] # Order object is same for all rows
    
    status = "Pending"
    
    # Check if any route is active or completed
    # If multiple routes (unlikely for MVP), prioritize active/completed.
    
    for row in rows:
        _, route_status, stop_status = row
        
        if route_status:
            if route_status == RouteStatus.PLANNED:
                if status == "Pending": # Only upgrade from Pending
                    status = "Assigned"
            elif route_status == RouteStatus.ACTIVE:
                if status in ["Pending", "Assigned"]:
                    status = "In Transit"
            elif route_status == RouteStatus.COMPLETED:
                 # If route is completed, order is likely completed, unless we want to be specific about drop off.
                 status = "Completed"
            
            if stop_status == StopStatus.COMPLETED:
                 status = "Completed"

    return OrderResponse(
        id=order.id,
        email_id=order.email_id,
        customer=order.email_sender,
        loading_address=order.loading_address,
        unloading_address=order.unloading_address,
        loading_date=order.loading_date,
        unloading_date=order.unloading_date,
        status=status
    )
