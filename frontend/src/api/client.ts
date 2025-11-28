import axios from 'axios';

export interface Order {
    id: number;
    email_id: string;
    customer: string;
    loading_address: string;
    unloading_address: string;
    loading_date: string;
    unloading_date: string;
    status: 'Pending' | 'Assigned' | 'In Transit' | 'Completed' | 'Cancelled';
}

export type TruckStatus = "AVAILABLE" | "MAINTENANCE" | "OUT_OF_SERVICE" | "INACTIVE";

export interface Truck {
    id: string;
    plate_number: string;
    trailer_plate_number?: string;
    capacity_weight: number;
    status: TruckStatus;
    is_active: boolean;
    current_location?: string;
    assigned_driver?: string;
}

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://api.valdanktrading.org');

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Send cookies with cross-origin requests
});

export const fetchOrders = async (): Promise<Order[]> => {
    const response = await apiClient.get<Order[]>('/orders/');
    return response.data;
};

export const fetchOrder = async (id: number): Promise<Order> => {
    const response = await apiClient.get<Order>(`/orders/${id}`);
    return response.data;
};

// Truck APIs
export const fetchTrucks = async (): Promise<Truck[]> => {
    const response = await apiClient.get<Truck[]>('/trucks/');
    return response.data;
};

export const createTruck = async (truck: Omit<Truck, 'id'>): Promise<Truck> => {
    const response = await apiClient.post<Truck>('/trucks/', truck);
    return response.data;
};

export const updateTruck = async (id: string, truck: Partial<Truck>): Promise<Truck> => {
    const response = await apiClient.put<Truck>(`/trucks/${id}`, truck);
    return response.data;
};

export const deleteTruck = async (id: string): Promise<void> => {
    await apiClient.delete(`/trucks/${id}`);
};

export interface RoutePlanRequest {
    truck_id: string;
    date: string; // ISO 8601
    order_ids: number[];
}

export const createRoutePlan = async (plan: RoutePlanRequest): Promise<any> => {
    const response = await apiClient.post('/routes/plan', plan);
    return response.data;
};
