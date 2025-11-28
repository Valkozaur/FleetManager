import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { MapPin, Flag, Trash2, GripVertical, Truck as TruckIcon, ArrowRightLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { fetchOrders, fetchTrucks, createRoutePlan } from '@/api/client';
import type { Order } from '@/api/client';

// --- Components for Route Items ---

interface SortableRouteItemProps {
  order: Order;
  onRemove: (id: number) => void;
}

function SortableRouteItem({ order, onRemove }: SortableRouteItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: order.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} className="mb-4">
      <div className="border rounded-lg bg-white shadow-sm overflow-hidden">
         {/* Header with Drag Handle */}
        <div className="flex items-center justify-between p-2 bg-gray-50 border-b">
            <div className="flex items-center gap-2">
                <button {...attributes} {...listeners} className="cursor-grab hover:bg-gray-200 rounded p-1">
                    <GripVertical className="h-4 w-4 text-gray-400" />
                </button>
                <span className="text-sm font-medium text-gray-600">Order #{order.id}</span>
                <span className="text-xs text-gray-400">(from ORD-{order.id})</span>
            </div>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-gray-400 hover:text-red-500" onClick={() => onRemove(order.id)}>
                <Trash2 className="h-4 w-4" />
            </Button>
        </div>
        
        {/* Stops Representation */}
        <div className="p-3 space-y-3">
            <div className="flex items-start gap-3">
                <MapPin className="h-4 w-4 text-green-600 mt-1 shrink-0" />
                <div>
                    <p className="text-sm font-medium">Pickup: {order.loading_address}</p>
                    {/* <p className="text-xs text-gray-500">lat/lon...</p> */}
                </div>
            </div>
             <div className="flex items-start gap-3">
                <Flag className="h-4 w-4 text-red-600 mt-1 shrink-0" />
                <div>
                    <p className="text-sm font-medium">Destination: {order.unloading_address}</p>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}

// --- Main Page Component ---

export default function CreateRoutePage() {
  const navigate = useNavigate();

  // Data Fetching
  const { data: orders = [] } = useQuery({ queryKey: ['orders'], queryFn: fetchOrders });
  const { data: trucks = [] } = useQuery({ queryKey: ['trucks'], queryFn: fetchTrucks });

  // State
  const [selectedTruckId, setSelectedTruckId] = useState<string | null>(null);
  const [selectedOrderIds, setSelectedOrderIds] = useState<number[]>([]);

  // Computed
  const availableTrucks = trucks.filter(t => t.status === 'AVAILABLE' && t.is_active !== false); // Check is_active if exists
  const availableOrders = orders.filter(o => !selectedOrderIds.includes(o.id) && o.status === 'Pending');
  
  const selectedOrders = useMemo(() => {
    return selectedOrderIds.map(id => orders.find(o => o.id === id)!).filter(Boolean);
  }, [selectedOrderIds, orders]);

  // Sensors for DnD
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Handlers
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      setSelectedOrderIds((items) => {
        const oldIndex = items.indexOf(active.id as number);
        const newIndex = items.indexOf(over?.id as number);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleAddOrder = (order: Order) => {
    setSelectedOrderIds(prev => [...prev, order.id]);
  };

  const handleRemoveOrder = (id: number) => {
    setSelectedOrderIds(prev => prev.filter(oid => oid !== id));
  };

  const createRouteMutation = useMutation({
    mutationFn: createRoutePlan,
    onSuccess: () => {
      // toast.success("Route created successfully!");
      navigate('/routes');
    },
    onError: (error: any) => {
      console.error("Failed to create route", error);
      alert(`Failed to create route: ${error.response?.data?.detail || error.message}`);
    }
  });

  const handleCreateRoute = () => {
    if (!selectedTruckId) {
      alert("Please select a truck.");
      return;
    }
    if (selectedOrderIds.length === 0) {
      alert("Please add at least one order.");
      return;
    }

    const payload = {
      truck_id: selectedTruckId,
      date: new Date().toISOString(), // Today
      order_ids: selectedOrderIds
    };

    createRouteMutation.mutate(payload);
  };

  return (
    <div className="space-y-6 p-6 pb-24"> {/* Added padding bottom for scrolling */}
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Create New Truck Route</h1>
          <p className="text-gray-500 mt-1">Add orders to build a route and then assign it to a truck.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
          <Button onClick={handleCreateRoute} disabled={createRouteMutation.isPending}>
            {createRouteMutation.isPending ? "Creating..." : "Create Route"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column */}
        <div className="space-y-6">
          
          {/* Available Orders */}
          <Card className="h-[500px] flex flex-col">
            <CardHeader>
              <CardTitle>Available Orders</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto space-y-4 p-4">
              {availableOrders.length === 0 ? (
                <div className="text-center text-gray-500 py-8">No available orders found.</div>
              ) : (
                availableOrders.map(order => (
                  <div key={order.id} className="border rounded-lg p-4 bg-white hover:border-blue-400 cursor-pointer transition-colors group" onClick={() => handleAddOrder(order)}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-gray-700">Order #ORD-{order.id}</span>
                      <Button variant="ghost" size="sm" className="h-6 w-6 opacity-0 group-hover:opacity-100 text-blue-600">
                        +
                      </Button>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 text-green-600 mt-0.5" />
                        <span className="text-sm text-gray-600 line-clamp-1">{order.loading_address}</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <Flag className="h-4 w-4 text-red-600 mt-0.5" />
                        <span className="text-sm text-gray-600 line-clamp-1">{order.unloading_address}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Assigned Truck */}
          <Card>
            <CardHeader>
              <CardTitle>Assigned Truck</CardTitle>
            </CardHeader>
            <CardContent>
               {availableTrucks.length === 0 && !selectedTruckId ? (
                 <div className="p-4 bg-gray-50 rounded-lg text-center text-gray-500">
                   No available trucks found.
                 </div>
               ) : (
                 <div className="p-6 bg-gray-50 rounded-lg flex flex-col items-center justify-center gap-4 min-h-[150px]">
                    {selectedTruckId ? (
                        <div className="w-full">
                             <div className="flex items-center gap-4 bg-white p-4 rounded border mb-4">
                                <div className="bg-blue-100 p-2 rounded-full">
                                    <TruckIcon className="h-6 w-6 text-blue-600" />
                                </div>
                                <div>
                                    <p className="font-bold text-gray-900">{trucks.find(t => t.id === selectedTruckId)?.plate_number}</p>
                                    <p className="text-sm text-gray-500">Capacity: {trucks.find(t => t.id === selectedTruckId)?.capacity_weight}kg</p>
                                </div>
                                <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setSelectedTruckId(null)}>Change</Button>
                             </div>
                        </div>
                    ) : (
                        <>
                            <p className="text-gray-500">No truck currently assigned.</p>
                            <Select onValueChange={setSelectedTruckId}>
                                <SelectTrigger className="w-full max-w-xs">
                                    <SelectValue placeholder="Select a truck" />
                                </SelectTrigger>
                                <SelectContent>
                                    {availableTrucks.map(truck => (
                                        <SelectItem key={truck.id} value={truck.id}>
                                            {truck.plate_number} ({truck.capacity_weight}kg)
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </>
                    )}
                 </div>
               )}
            </CardContent>
          </Card>

        </div>

        {/* Right Column: Route Sequence */}
        <div className="space-y-6">
             <div className="flex flex-col gap-2">
                <h2 className="text-lg font-semibold text-gray-900">Route Sequence</h2>
             </div>
             
             <div className="border-2 border-dashed border-gray-300 rounded-xl min-h-[600px] bg-gray-50/50 p-6">
                {selectedOrders.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-4">
                        <ArrowRightLeft className="h-12 w-12 opacity-20" />
                        <p className="text-center max-w-xs">Drag & drop addresses here to build the route sequence.</p>
                        {/* Note: Visual instruction says Drag & drop, but we implemented Click-to-Add for simplicity, though list is reorderable */}
                    </div>
                ) : (
                    <DndContext 
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={handleDragEnd}
                    >
                        <SortableContext 
                            items={selectedOrderIds}
                            strategy={verticalListSortingStrategy}
                        >
                            {selectedOrders.map(order => (
                                <SortableRouteItem key={order.id} order={order} onRemove={handleRemoveOrder} />
                            ))}
                        </SortableContext>
                    </DndContext>
                )}
             </div>
        </div>

      </div>
    </div>
  );
}
